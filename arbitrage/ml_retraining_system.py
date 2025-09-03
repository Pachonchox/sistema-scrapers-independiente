# -*- coding: utf-8 -*-
"""
🧠 SISTEMA DE REENTRENAMIENTO ML PARA ARBITRAJE
==============================================

Reentrena el modelo de Machine Learning con los nuevos campos disponibles
en el master system. El modelo anterior fue entrenado con menos campos.

Nuevos campos disponibles:
- storage, ram, screen_size (especificaciones técnicas)
- camera, front_camera (características)
- color, colors (variantes)
- rating, reviews_count (valoraciones)
- badges, emblems (etiquetas comerciales)
- metadata (datos JSON adicionales)
- fecha_captura, veces_visto (métricas temporales)
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    import joblib
except ImportError as e:
    print(f"❌ Dependencias ML no disponibles: {e}")
    print("Instalar con: pip install scikit-learn pandas joblib")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    print("WARNING: SentenceTransformers no disponible - usando features tradicionales")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLRetrainingSystem:
    """
    🚀 Sistema de reentrenamiento del modelo ML de matching
    
    Características:
    - ✅ Utiliza TODOS los campos nuevos del master system
    - ✅ Genera features avanzadas
    - ✅ Entrena múltiples algoritmos (GBM, RF, LR)
    - ✅ Evaluación completa con métricas
    - ✅ Guarda modelos entrenados
    - ✅ Actualiza reglas de matching
    """
    
    def __init__(self, db_params: Dict[str, Any]):
        self.db_params = db_params
        self.conn = None
        self.embedder = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.models = {}
        self.feature_importance = {}
        
        # Intentar cargar embedder
        if SentenceTransformer:
            try:
                self.embedder = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
                logger.info("✅ Embedder cargado para features de texto")
            except Exception as e:
                logger.warning(f"No se pudo cargar embedder: {e}")
    
    def connect(self):
        """Conecta a PostgreSQL"""
        self.conn = psycopg2.connect(**self.db_params, cursor_factory=RealDictCursor)
        logger.info("🔌 Conectado a PostgreSQL")
    
    def disconnect(self):
        """Desconecta de PostgreSQL"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Desconectado de PostgreSQL")
    
    def extract_training_data(self) -> pd.DataFrame:
        """
        Extrae datos de entrenamiento desde PostgreSQL usando TODOS los nuevos campos
        """
        logger.info("📊 Extrayendo datos de entrenamiento con campos expandidos...")
        
        cursor = self.conn.cursor()
        
        # Query con TODOS los campos nuevos
        cursor.execute("""
            SELECT 
                -- Campos básicos
                p.codigo_interno, p.nombre, p.marca, p.categoria, p.retailer,
                -- Especificaciones técnicas (NUEVOS)
                p.storage, p.ram, p.screen_size,
                -- Características visuales (NUEVOS)
                p.camera, p.front_camera, p.color, p.colors,
                -- Métricas comerciales (NUEVOS)
                p.rating, p.reviews_count, p.badges, p.emblems,
                -- Información de stock y descuentos (NUEVOS)
                p.out_of_stock, p.discount_percent, p.shipping_options,
                -- Métricas temporales (NUEVOS)
                p.fecha_primera_captura, p.fecha_ultima_actualizacion, 
                p.ultimo_visto, p.veces_visto,
                -- Datos normalizados (NUEVOS)
                p.nombre_normalizado, p.specs_hash, p.metadata,
                -- Precios actuales
                pr.precio_normal, pr.precio_oferta, pr.precio_min_dia
            FROM master_productos p
            LEFT JOIN master_precios pr ON p.codigo_interno = pr.codigo_interno 
                AND pr.fecha = CURRENT_DATE
            WHERE p.activo = true
                AND p.nombre IS NOT NULL
                AND LENGTH(TRIM(p.nombre)) > 10
            ORDER BY p.retailer, p.categoria
            LIMIT 1000
        """)
        
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        
        logger.info(f"📊 Extraídos {len(df)} productos con {len(df.columns)} campos")
        logger.info(f"🏪 Retailers: {df['retailer'].value_counts().to_dict()}")
        
        return df
    
    def generate_enhanced_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Genera features avanzadas usando TODOS los campos nuevos
        """
        logger.info("🔧 Generando features ML avanzadas...")
        
        feature_list = []
        all_features = []
        
        # Generar pares de productos para comparación
        comparisons = []
        labels = []
        
        products = df.to_dict('records')
        
        for i, prod_a in enumerate(products):
            for j, prod_b in enumerate(products[i+1:], i+1):
                if prod_a['retailer'] != prod_b['retailer']:  # Solo cross-retailer
                    
                    # Generar features para este par
                    features = self._extract_pair_features(prod_a, prod_b)
                    
                    # Label: 1 si son el mismo producto, 0 si no
                    # Usamos heurística: misma marca + nombre similar + specs similares
                    is_match = self._determine_match_label(prod_a, prod_b)
                    
                    comparisons.append(features)
                    labels.append(is_match)
                    
                    if len(comparisons) >= 5000:  # Límite para no sobrecargar
                        break
            
            if len(comparisons) >= 5000:
                break
        
        logger.info(f"🎯 Generadas {len(comparisons)} comparaciones")
        logger.info(f"📊 Distribución labels: {pd.Series(labels).value_counts().to_dict()}")
        
        # Obtener nombres de features
        if comparisons:
            feature_names = list(comparisons[0].keys())
            
            # Convertir a arrays numpy
            X = np.array([[comp[fname] for fname in feature_names] for comp in comparisons])
            y = np.array(labels)
            
            return X, y, feature_names
        
        return np.array([]), np.array([]), []
    
    def _extract_pair_features(self, prod_a: Dict, prod_b: Dict) -> Dict[str, float]:
        """
        Extrae features de un par de productos usando TODOS los campos nuevos
        """
        features = {}
        
        # === FEATURES BÁSICAS (mejoradas) ===
        
        # Similitud de nombres con embedding si disponible
        if self.embedder and prod_a['nombre'] and prod_b['nombre']:
            try:
                emb_a = self.embedder.encode(prod_a['nombre'])
                emb_b = self.embedder.encode(prod_b['nombre'])
                features['text_similarity_embedding'] = float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b)))
            except:
                features['text_similarity_embedding'] = 0.0
        else:
            features['text_similarity_embedding'] = 0.0
        
        # Similitud de nombres tradicional (Jaccard)
        tokens_a = set((prod_a['nombre'] or '').lower().split())
        tokens_b = set((prod_b['nombre'] or '').lower().split())
        if tokens_a and tokens_b:
            features['text_similarity_jaccard'] = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        else:
            features['text_similarity_jaccard'] = 0.0
        
        # Match exacto de marca
        marca_a = (prod_a['marca'] or '').upper().strip()
        marca_b = (prod_b['marca'] or '').upper().strip() 
        features['brand_exact_match'] = 1.0 if marca_a and marca_b and marca_a == marca_b else 0.0
        
        # === FEATURES TÉCNICAS NUEVAS ===
        
        # Storage matching
        storage_a = self._normalize_storage(prod_a['storage'])
        storage_b = self._normalize_storage(prod_b['storage'])
        features['storage_match'] = 1.0 if storage_a and storage_b and storage_a == storage_b else 0.0
        features['storage_available'] = 1.0 if storage_a or storage_b else 0.0
        
        # RAM matching  
        ram_a = self._normalize_ram(prod_a['ram'])
        ram_b = self._normalize_ram(prod_b['ram'])
        features['ram_match'] = 1.0 if ram_a and ram_b and ram_a == ram_b else 0.0
        features['ram_available'] = 1.0 if ram_a or ram_b else 0.0
        
        # Screen size matching
        screen_a = self._normalize_screen(prod_a['screen_size'])
        screen_b = self._normalize_screen(prod_b['screen_size'])
        features['screen_match'] = 1.0 if screen_a and screen_b and abs(screen_a - screen_b) <= 0.5 else 0.0
        features['screen_available'] = 1.0 if screen_a or screen_b else 0.0
        
        # Color matching
        color_a = (prod_a['color'] or '').lower().strip()
        color_b = (prod_b['color'] or '').lower().strip()
        features['color_match'] = 1.0 if color_a and color_b and color_a == color_b else 0.0
        
        # === FEATURES COMERCIALES NUEVAS ===
        
        # Rating proximity
        rating_a = float(prod_a['rating'] or 0)
        rating_b = float(prod_b['rating'] or 0)
        if rating_a > 0 and rating_b > 0:
            features['rating_diff'] = abs(rating_a - rating_b)
            features['rating_available'] = 1.0
        else:
            features['rating_diff'] = 0.0
            features['rating_available'] = 0.0
        
        # Reviews count ratio
        reviews_a = int(prod_a['reviews_count'] or 0)
        reviews_b = int(prod_b['reviews_count'] or 0)
        if reviews_a > 0 and reviews_b > 0:
            features['reviews_ratio'] = min(reviews_a, reviews_b) / max(reviews_a, reviews_b)
        else:
            features['reviews_ratio'] = 0.0
        
        # Stock status matching
        stock_a = not (prod_a['out_of_stock'] or False)
        stock_b = not (prod_b['out_of_stock'] or False)
        features['both_in_stock'] = 1.0 if stock_a and stock_b else 0.0
        
        # === FEATURES DE PRECIOS MEJORADAS ===
        
        # Precio ratio más sofisticado
        precio_a = float(prod_a['precio_min_dia'] or 0)
        precio_b = float(prod_b['precio_min_dia'] or 0)
        
        if precio_a > 0 and precio_b > 0:
            ratio = min(precio_a, precio_b) / max(precio_a, precio_b)
            features['price_ratio'] = ratio
            features['price_diff_percent'] = abs(precio_a - precio_b) / ((precio_a + precio_b) / 2) * 100
            features['price_available'] = 1.0
        else:
            features['price_ratio'] = 0.0
            features['price_diff_percent'] = 0.0
            features['price_available'] = 0.0
        
        # === FEATURES TEMPORALES NUEVAS ===
        
        # Veces visto similarity 
        veces_a = int(prod_a['veces_visto'] or 1)
        veces_b = int(prod_b['veces_visto'] or 1)
        features['popularity_ratio'] = min(veces_a, veces_b) / max(veces_a, veces_b)
        
        # Categoría matching
        cat_a = (prod_a['categoria'] or '').lower()
        cat_b = (prod_b['categoria'] or '').lower()
        features['category_match'] = 1.0 if cat_a and cat_b and cat_a == cat_b else 0.0
        
        return features
    
    def _determine_match_label(self, prod_a: Dict, prod_b: Dict) -> int:
        """
        Determina si dos productos son el mismo (heurística para generar labels)
        """
        # Heurística conservadora para generar labels de entrenamiento
        
        # 1. Misma marca es obligatorio
        marca_a = (prod_a['marca'] or '').upper().strip()
        marca_b = (prod_b['marca'] or '').upper().strip()
        if not (marca_a and marca_b and marca_a == marca_b):
            return 0
        
        # 2. Similitud alta de nombre
        nombre_a = (prod_a['nombre'] or '').lower()
        nombre_b = (prod_b['nombre'] or '').lower()
        tokens_a = set(nombre_a.split())
        tokens_b = set(nombre_b.split())
        
        if tokens_a and tokens_b:
            jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
            if jaccard < 0.6:
                return 0
        
        # 3. Al menos una spec técnica debe coincidir (si está disponible)
        storage_match = False
        ram_match = False
        screen_match = False
        
        # Storage
        storage_a = self._normalize_storage(prod_a['storage'])
        storage_b = self._normalize_storage(prod_b['storage'])
        if storage_a and storage_b:
            storage_match = (storage_a == storage_b)
        
        # RAM
        ram_a = self._normalize_ram(prod_a['ram'])
        ram_b = self._normalize_ram(prod_b['ram'])
        if ram_a and ram_b:
            ram_match = (ram_a == ram_b)
        
        # Screen
        screen_a = self._normalize_screen(prod_a['screen_size'])
        screen_b = self._normalize_screen(prod_b['screen_size'])
        if screen_a and screen_b:
            screen_match = (abs(screen_a - screen_b) <= 0.5)
        
        # Si hay specs disponibles, al menos una debe coincidir
        specs_available = any([storage_a and storage_b, ram_a and ram_b, screen_a and screen_b])
        specs_match = any([storage_match, ram_match, screen_match])
        
        if specs_available and not specs_match:
            return 0
        
        # 4. Precios no pueden ser demasiado diferentes (factor 3x máximo)
        precio_a = float(prod_a['precio_min_dia'] or 0)
        precio_b = float(prod_b['precio_min_dia'] or 0)
        
        if precio_a > 0 and precio_b > 0:
            ratio = max(precio_a, precio_b) / min(precio_a, precio_b)
            if ratio > 3.0:  # Más de 3x diferencia = productos diferentes
                return 0
        
        # Si pasa todos los filtros, probablemente es el mismo producto
        return 1
    
    def _normalize_storage(self, storage_str: str) -> Optional[int]:
        """Normaliza string de storage a GB"""
        if not storage_str:
            return None
        
        s = str(storage_str).upper()
        
        # Buscar números + TB/GB
        import re
        if 'TB' in s:
            match = re.search(r'(\d+)', s)
            if match:
                return int(match.group(1)) * 1000  # TB a GB
        elif 'GB' in s:
            match = re.search(r'(\d+)', s)
            if match:
                return int(match.group(1))
        
        return None
    
    def _normalize_ram(self, ram_str: str) -> Optional[int]:
        """Normaliza string de RAM a GB"""
        if not ram_str:
            return None
        
        s = str(ram_str).upper()
        
        import re
        match = re.search(r'(\d+)', s)
        if match:
            return int(match.group(1))
        
        return None
    
    def _normalize_screen(self, screen_str: str) -> Optional[float]:
        """Normaliza string de pantalla a pulgadas"""
        if not screen_str:
            return None
        
        s = str(screen_str)
        
        import re
        match = re.search(r'(\d+\.?\d*)', s)
        if match:
            return float(match.group(1))
        
        return None
    
    def train_models(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """
        Entrena múltiples modelos ML
        """
        logger.info("🚀 Entrenando modelos ML...")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Normalizar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {}
        
        # 1. Gradient Boosting (mejor para features mixtas)
        logger.info("📈 Entrenando Gradient Boosting...")
        gbm = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        gbm.fit(X_train, y_train)
        
        y_pred_gbm = gbm.predict(X_test)
        y_proba_gbm = gbm.predict_proba(X_test)[:, 1]
        
        self.models['gradient_boosting'] = gbm
        self.feature_importance['gradient_boosting'] = dict(zip(feature_names, gbm.feature_importances_))
        
        results['gradient_boosting'] = {
            'accuracy': gbm.score(X_test, y_test),
            'auc': roc_auc_score(y_test, y_proba_gbm),
            'classification_report': classification_report(y_test, y_pred_gbm, output_dict=True)
        }
        
        # 2. Random Forest 
        logger.info("🌳 Entrenando Random Forest...")
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        rf.fit(X_train, y_train)
        
        y_pred_rf = rf.predict(X_test)
        y_proba_rf = rf.predict_proba(X_test)[:, 1]
        
        self.models['random_forest'] = rf
        self.feature_importance['random_forest'] = dict(zip(feature_names, rf.feature_importances_))
        
        results['random_forest'] = {
            'accuracy': rf.score(X_test, y_test),
            'auc': roc_auc_score(y_test, y_proba_rf),
            'classification_report': classification_report(y_test, y_pred_rf, output_dict=True)
        }
        
        # 3. Logistic Regression (baseline)
        logger.info("📊 Entrenando Logistic Regression...")
        lr = LogisticRegression(random_state=42, max_iter=1000)
        lr.fit(X_train_scaled, y_train)
        
        y_pred_lr = lr.predict(X_test_scaled)
        y_proba_lr = lr.predict_proba(X_test_scaled)[:, 1]
        
        self.models['logistic_regression'] = lr
        
        results['logistic_regression'] = {
            'accuracy': lr.score(X_test_scaled, y_test),
            'auc': roc_auc_score(y_test, y_proba_lr),
            'classification_report': classification_report(y_test, y_pred_lr, output_dict=True)
        }
        
        logger.info("✅ Modelos entrenados")
        return results
    
    def save_models(self, models_dir: str = 'models/retrained'):
        """Guarda los modelos entrenados"""
        os.makedirs(models_dir, exist_ok=True)
        
        # Guardar modelos
        for name, model in self.models.items():
            model_path = os.path.join(models_dir, f'{name}_model.joblib')
            joblib.dump(model, model_path)
            logger.info(f"💾 Modelo {name} guardado en {model_path}")
        
        # Guardar scaler
        scaler_path = os.path.join(models_dir, 'scaler.joblib')
        joblib.dump(self.scaler, scaler_path)
        
        # Guardar feature importance
        importance_path = os.path.join(models_dir, 'feature_importance.json')
        with open(importance_path, 'w', encoding='utf-8') as f:
            json.dump(self.feature_importance, f, indent=2, ensure_ascii=False)
        
        # Actualizar reglas de matching
        self._update_matching_rules(models_dir)
        
        logger.info(f"💾 Modelos completos guardados en {models_dir}")
    
    def _update_matching_rules(self, models_dir: str):
        """Actualiza las reglas de matching basadas en feature importance"""
        
        # Obtener importancias del mejor modelo (GBM típicamente)
        if 'gradient_boosting' in self.feature_importance:
            importance = self.feature_importance['gradient_boosting']
            
            # Crear nuevas reglas basadas en importancia
            new_rules = {
                'similarity_weights': {},
                'feature_importance': importance,
                'model_version': datetime.now().isoformat(),
                'enhanced_features': True
            }
            
            # Mapear features importantes a pesos
            total_importance = sum(importance.values())
            
            for feature, imp in importance.items():
                weight = imp / total_importance
                
                if 'text_similarity' in feature:
                    new_rules['similarity_weights']['text'] = new_rules['similarity_weights'].get('text', 0) + weight
                elif 'brand' in feature:
                    new_rules['similarity_weights']['brand'] = new_rules['similarity_weights'].get('brand', 0) + weight
                elif any(spec in feature for spec in ['storage', 'ram', 'screen']):
                    new_rules['similarity_weights']['specs'] = new_rules['similarity_weights'].get('specs', 0) + weight
                elif 'price' in feature:
                    new_rules['similarity_weights']['price'] = new_rules['similarity_weights'].get('price', 0) + weight
                elif 'category' in feature:
                    new_rules['similarity_weights']['category'] = new_rules['similarity_weights'].get('category', 0) + weight
            
            # Normalizar pesos
            total_weight = sum(new_rules['similarity_weights'].values())
            if total_weight > 0:
                for key in new_rules['similarity_weights']:
                    new_rules['similarity_weights'][key] /= total_weight
            
            # Guardar reglas actualizadas
            rules_path = os.path.join(models_dir, 'enhanced_matching_rules.json')
            with open(rules_path, 'w', encoding='utf-8') as f:
                json.dump(new_rules, f, indent=2, ensure_ascii=False)
            
            logger.info(f"🔧 Reglas de matching actualizadas en {rules_path}")
    
    def run_full_retraining(self) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de reentrenamiento
        """
        logger.info("🚀 INICIANDO REENTRENAMIENTO COMPLETO DEL ML")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            self.connect()
            
            # 1. Extraer datos con nuevos campos
            logger.info("📊 Fase 1: Extrayendo datos con campos expandidos...")
            df = self.extract_training_data()
            
            # 2. Generar features avanzadas
            logger.info("🔧 Fase 2: Generando features ML avanzadas...")
            X, y, feature_names = self.generate_enhanced_features(df)
            
            if len(X) == 0:
                raise Exception("No se pudieron generar features de entrenamiento")
            
            # 3. Entrenar modelos
            logger.info("🚀 Fase 3: Entrenando modelos ML...")
            results = self.train_models(X, y, feature_names)
            
            # 4. Guardar modelos
            logger.info("💾 Fase 4: Guardando modelos entrenados...")
            self.save_models()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info("✅ REENTRENAMIENTO COMPLETADO")
            logger.info(f"⏱️ Duración total: {duration:.2f}s")
            
            return {
                'success': True,
                'duration_seconds': duration,
                'samples_trained': len(X),
                'features_count': len(feature_names),
                'model_results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en reentrenamiento: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        finally:
            self.disconnect()

def main():
    """Función principal"""
    
    db_params = {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', '5434'))  # Updated to match docker-compose.yml,
        'database': os.environ.get('PGDATABASE', 'price_orchestrator'),
        'user': os.environ.get('PGUSER', 'orchestrator'),
        'password': os.environ.get('PGPASSWORD', 'orchestrator_2025')
    }
    
    retrainer = MLRetrainingSystem(db_params)
    result = retrainer.run_full_retraining()
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"✅ Éxito: {result['success']}")
    if result['success']:
        print(f"⏱️ Duración: {result['duration_seconds']:.2f}s")
        print(f"📊 Samples: {result['samples_trained']}")
        print(f"🔧 Features: {result['features_count']}")
        print(f"🎯 Modelos entrenados: {len(result['model_results'])}")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()