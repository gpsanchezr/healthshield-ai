# scripts/

Este directorio agrupa wrappers y utilidades para ejecutar tareas repetidas sin tocar el código del backend.

## Uso

### Ejecutar ETL

```powershell
python scripts/etl/run_etl.py --file datasets/clinical_data_v1.0_raw.xlsx
```

### Entrenar el modelo ML

```powershell
python scripts/ml/train_model.py --algorithm random_forest
```

### Ejecutar pruebas

```powershell
python scripts/test/run_pytest.py
```

## Objetivo

- Facilitar la ejecución local para desarrolladores nuevos.
- Permitir reproducir el pipeline sin abrir `manage.py` directamente.
- Mantener la lógica de arranque separada del código de negocio.
