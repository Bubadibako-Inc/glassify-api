# glassify-api

## To install requirements, run in terminal:
```
pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```

## To generate a secure JWT secret key, run in terminal:
```
python
```
or
```
python3
```
then:
```
import secrets
print(secrets.token_urlsafe(32))
```
Copy the generated key and paste it as the value for `JWT_SECRET_KEY`

## Last, run the `run.py`:
```
python run.py
```
or
```
python3 run.py
```
