from fastapi import FastAPI, HTTPException, UploadFile, File
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import boto3
import os

import smtplib
from email.mime.text import MIMEText


app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")

DB_USER = os.environ.get("DB_USER")
DB_SERVER = os.environ.get("DB_SERVER")
DB_NAME = os.environ.get("DB_NAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
S3_BUCKET = os.environ.get("S3_BUCKET")
REGION = os.environ.get("REGION")
SMTP_SECRET = os.environ.get("SMTP_SECRET")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER").split(', ')


print("SMTP SECRET", SMTP_SECRET)
print("SMTP_PASSWORD", SMTP_PASSWORD)
print("SMTP_SERVER", SMTP_SERVER)

# SMTP server details
# SMTP_SERVER = "email-smtp.us-east-1.amazonaws.com"
SMTP_PORT = 587

if DB_USER is None:
    raise EnvironmentError("DB_USER environment variable not set")

if DB_SERVER is None:
    raise EnvironmentError("DB_SERVER environment variable not set")

if DB_NAME is None:
    raise EnvironmentError("DB_NAME environment variable not set")

if DB_PASSWORD is None:
    raise EnvironmentError("DB_PASSWORD environment variable not set")

if S3_BUCKET is None:
    raise EnvironmentError("S3_BUCKET environment variable not set")

if REGION is None:
    raise EnvironmentError("REGION environment variable not set")


conn_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"

# Create a SQLAlchemy engine
engine = create_engine(conn_string)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# s3 = boto3.resource('s3')
# bucket = s3.Bucket(S3_BUCKET)


s3 = boto3.client('s3')
ses_client = boto3.client('ses', region_name=REGION)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, Sequence("item_id_seq"), primary_key=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)

@app.get("/api/")
async def main():
    return {"message": "Test of container deployment"}

@app.post("/api/create_item/")
async def create_item(name: str):
    try:
        db = SessionLocal()
        new_item = Item(name=name)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Item creation failed")

@app.post("/api/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        s3.upload_fileobj(file.file, S3_BUCKET, file.filename)
        return {"filename": file.filename}
    except Exception as e:
        return {"message": str(e)}

@app.get("/api/list_files/")
async def get_files():
    return {"filenames": s3.list_objects(Bucket=S3_BUCKET)}



@app.post("/api/send_email/")
async def send_email(sender: str, recipient: str, subject="", body=""):

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        server = smtplib.SMTP(SMTP_SERVER[0], SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_SECRET, SMTP_PASSWORD)
        server.sendmail(sender, recipient, msg.as_string())
        server.close()
        return {"message": "Email sent successfully!"}
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Something went wrong")
