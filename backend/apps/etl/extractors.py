import pandas as pd


class CSVExtractor:
    def extract(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path)


class ExcelExtractor:
    def extract(self, path: str) -> pd.DataFrame:
        # Primera hoja por defecto
        return pd.read_excel(path)

