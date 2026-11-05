from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import auth
import models
import schemas
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI JWT Microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(auth.get_db)):
    db_user = db.query(models.User).filter((models.User.username == user.username) | (models.User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.UserLogin, db: Session = Depends(auth.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/items", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    new_item = models.Item(**item.model_dump(), owner_id=current_user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.get("/items", response_model=list[schemas.ItemResponse])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(auth.get_db)):
    return db.query(models.Item).offset(skip).limit(limit).all()

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: int, db: Session = Depends(auth.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id: int, updated: schemas.ItemCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id, models.Item.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized")
    for key, value in updated.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id, models.Item.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}
