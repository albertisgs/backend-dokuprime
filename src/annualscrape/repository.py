# src/annualscrape/repository.py

import psycopg2
import os
from datetime import datetime 
from dotenv import load_dotenv

load_dotenv()

class ScrapperRepository:
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        
    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host="localhost",
            port=self.port
        )

    def insert_db_forHK(self) -> bool: # Added return type hint
        conn = None # Initialize conn to None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
           # Get the current timestamp to use for all inserts
            now = datetime.now()

            # INSERT INTO KNOWLEDGE BASE
            insert_query = """
                INSERT INTO knowledge_base (id, company_name, report_title, year, upload_date, status, file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # Use the 'now' variable for the upload_date
            data_list = [
                (16, "PT Hutama Karya (Persero) Tbk", "Annual Report 2024", 2024, now, "Completed", "/file_annual_report/Hutama/AR2024.pdf" ),
                (17, "PT Hutama Karya (Persero) Tbk", "Annual Report 2023", 2023, now, "Completed", "/file_annual_report/Hutama/AR2023.pdf" ),
                (18, "PT Hutama Karya (Persero) Tbk", "Annual Report 2022", 2022, now, "Completed", "/file_annual_report/Hutama/AR2022.pdf" ),
                (19, "PT Hutama Karya (Persero) Tbk", "Annual Report 2021", 2021, now, "Completed", "/file_annual_report/Hutama/AR2021.pdf" ),
                (20, "PT Hutama Karya (Persero) Tbk", "Annual Report 2020", 2020, now, "Completed", "/file_annual_report/Hutama/AR2020.pdf" ),
            ]

            # INSERT INTO DASHBOARD - FINANCIAL
            insert_query1 = """
                INSERT INTO public.financials
                (id, company_name, total_assets, total_equity, total_revenue, gross_profit, net_income, cost_of_revenues, account_receivables_third_party, account_recevables_related_party, gross_receivables_third_party, gross_receivables_related_party, inventory, current_assets, inventory_current, cash_and_equivalents, current_liabilities, created_at, roa, roe, gross_margin, net_margin, asset_turnover, receivables_turnover, inventory_turnover, current_ratio, quick_ratio, cash_ratio, average_inventory, average_receivables, total_receivables, profit, liquid, efficient, average_score, "year")
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data_list1 = [
                (25, 'PT. Hutama Karya', None, None, None, None, None, None, 233978.00, 1252388.00, 341832.00, 2513224.00, 889865.00, None, None, None, None, '2025-07-09 14:50:09.260', None, None, None, None, None, None, None, None, None, None, None, None, 4341422.00, 0.00, 0.00, 0.00, 0.00, '2019-01-01 00:00:00.000'),
                (26, 'PT. Hutama Karya', 132917503.00, 54808750.00, 20484998.00, 2351392.00, 2449897.00, 18133606.00, 185450.00, 395263.00, 318004.00, 1605503.00, 939536.00, 28206904.00, None, 21205226.00, 26708953.00, '2025-07-09 14:50:18.878', 1.8400, 4.4700, 11.4800, 11.9600, 0.1541, 6.0117, 20.5354, 1.0561, 1.0209, 0.7939, 883042.00, 3407533.00, 2504220.00, 6.61, 0.99, 8.61, 5.40, '2021-01-01 00:00:00.000'),
                (27, 'PT. Hutama Karya', 110989762.00, 31799462.00, 21642841.00, 1866132.00, 2098133.00, 19776709.00, 211557.00, 907503.00, 394657.00, 2797129.00, 826548.00, 23767820.00, None, 11127374.00, 38093957.00, '2025-07-09 14:48:42.206', 1.8900, 6.6000, 8.6200, 9.6900, 0.1950, 5.0028, 23.0442, 0.6239, 0.6022, 0.2921, 858206.50, 4326134.00, 4310846.00, 6.26, 0.55, 8.97, 5.26, '2020-01-01 00:00:00.000'),
                (28, 'PT. Hutama Karya', 156316417.00, 84779539.00, 24208538.00, 3611900.00, 1446602.00, 20596638.00, 118205.00, 444453.00, 466042.00, 2007772.00, 767063.00, 40836176.00, None, 33906186.00, 20723714.00, '2025-07-09 14:50:22.750', 0.9300, 1.7100, 14.9200, 5.9800, 0.1549, 8.7385, 24.1376, 1.9705, 1.9335, 1.6361, 853299.50, 2770346.00, 3036472.00, 4.53, 1.89, 10.78, 5.73, '2022-01-01 00:00:00.000'),
                (29, 'PT. Hutama Karya', 169739487.00, 116624513.00, 26926321.00, 2357794.00, 1914174.00, 24568527.00, 414910.00, 714461.00, 674124.00, 1867030.00, 495274.00, 49614335.00, None, 39059927.00, 21820021.00, '2025-07-09 14:50:25.448', 1.1300, 1.6400, 8.7600, 7.1100, 0.1586, 8.0293, 38.9255, 2.2738, 2.2511, 1.7901, 631168.50, 3353498.50, 3670525.00, 3.92, 2.17, 14.94, 7.01, '2023-01-01 00:00:00.000'),
                (30, 'PT. Hutama Karya', 196042463.00, 138000451.00, 30252293.00, 4274022.00, 2736669.00, 25978271.00, 366567.00, 690303.00, 523881.00, 2890180.00, 360019.00, 56457972.00, None, 36769029.00, 26406169.00, '2025-07-09 14:50:28.710', 1.4000, 1.9800, 14.1300, 9.0500, 0.1543, 7.4317, 60.7471, 2.1381, 2.1244, 1.3924, 427646.50, 4070728.00, 4470931.00, 5.40, 1.98, 21.24, 9.54, '2024-01-01 00:00:00.000'),
            ]

            # INSERT INTO DASHBOARD - KEYINSIGHT
            insert_query2 = """
                INSERT INTO public.dashboard_keyinsight
                ("VizId", "Visualization", "KeyInsight", "Year")
                VALUES(%s, %s, %s, %s);
            """
            data_list2 = [
                (0, 'Profitabilitas Perusahaan ', 'PT. Hutama Karya memiliki profitabilitas terendah dengan ROE 1,9% dan Net Margin hanya 0,9%, menandakan perlunya peningkatan dalam strategi bisnis dan efisiensi pengelolaan biaya.', None),
                (1, 'Tren ROA', 'PT. Hutama Karya mencatat ROA yang fluktuatif, tanpa tren pertumbuhan yang berkelanjutan.', None),
                (2, 'Efisiensi Operasional', 'PT. Hutama Karya mencatat Inventory Turnover sangat tinggi sebesar 60,75, menandakan siklus persediaan yang sangat cepat, tetapi perlu dicermati apakah ini berkontribusi terhadap profitabilitas.', None),
                (3, 'Likuiditas Perbandingan', 'PT. Hutama Karya memiliki Cash Ratio tertinggi (1,39) tetapi Current Ratio-nya 2,14, menunjukkan bahwa kas mendominasi aset lancar yang dimiliki.', None),
                (4, 'Summary', 'PT. Hutama Karya perlu menyeimbangkan efisiensi operasional dengan pencapaian laba.', None),
            ]

            # Eksekusi dan commit
            cur.executemany(insert_query, data_list)
            cur.executemany(insert_query1, data_list1)
            cur.executemany(insert_query2, data_list2)
            conn.commit()
            print(f"Database transaction for Hutama Karya successful. {cur.rowcount} rows inserted in the last operation.")
            return True # <-- Return True on success
        except Exception as e:
            print("Database Error:", e)
            if conn:
                conn.rollback()
            return False # <-- Return False on error
        finally:
            if conn:
                cur.close()
                conn.close()