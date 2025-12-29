
SwingBot ML – Full NSE/BSE Swing Scanner (Educational)

1. Create venv:
   python3 -m venv venv
   source venv/bin/activate  (Linux/mac)
   venv\Scripts\activate   (Windows)

2. Install deps:
   pip install -r requirements.txt

3. (Optional) Replace data/bse_symbols.csv with full BSE list.

4. Train model:
   python model_train.py

5. Run web app:
   python app.py

6. Open browser:
   http://127.0.0.1:5000
