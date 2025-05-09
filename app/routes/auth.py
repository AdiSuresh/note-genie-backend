from fastapi import APIRouter, HTTPException
from app.models.user.create import UserCreate
from app.models.user.login import UserLogin
from app.utils.auth import hash_password, verify_password
from app.utils.jwt import create_access_token
from app.core.database import users_collection

router = APIRouter()

@router.post('/sign-up')
async def sign_up(user: UserCreate):
    if await users_collection.find_one({'email': user.email}):
        raise HTTPException(status_code=400, detail='already_exists')
    hashed_pw = hash_password(user.password)
    await users_collection.insert_one({'email': user.email, 'hashed_password': hashed_pw})
    return {'message': 'success'}

@router.post('/sign-in')
async def sign_in(user: UserLogin):
    db_user = await users_collection.find_one({'email': user.email})
    if not db_user or not verify_password(user.password, db_user['hashed_password']):
        raise HTTPException(status_code=401, detail='invalid_credentials')
    token = create_access_token({'sub': user.email})
    return {'access_token': token, 'token_type': 'bearer'}
