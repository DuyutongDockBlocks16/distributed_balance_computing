import json
import os
from datetime import datetime

from flask import redirect

from serving import create_app

app = create_app()

@app.route("/health")
def health():
    return 'OK'


@app.route('/')
def home():
    return redirect('/api')


if __name__== '__main__':
  app.run(
      host = '0.0.0.0',
      port = 5000,  
      debug = True 
  )