from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.jwt import decode_token
from app.core.database import users_collection

def verify_token(token: str):
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
        )
    user_id: str = payload.get('sub')
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
        )
    return user_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='sign-in')

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = verify_token(token)

    try:
        user_id = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail='Invalid user ID') from e

    user = await users_collection.find_one({'_id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    return user
