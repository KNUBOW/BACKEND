from fastapi import APIRouter, UploadFile, Form, Depends, Query, status

from service.auth.jwt_handler import get_access_token
from service.board_service import BoardService
from core.di import get_board_service
router = APIRouter(prefix="/board", tags=["Board"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_board(
        title: str = Form(...),
        content: str = Form(...),
        images: list[UploadFile] = [],
        access_token: str = Depends(get_access_token),
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.create_board(access_token, title, content, images)


@router.get("/{board_id}")
async def get_board(
        board_id: int,
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.get_board(board_id)


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_boards(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1),
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.get_all_boards(skip=skip, limit=limit)


@router.patch("/{board_id}", status_code=status.HTTP_200_OK)
async def update_board(
        board_id: int,
        title: str | None = Form(None),
        content: str | None = Form(None),
        access_token: str = Depends(get_access_token),
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.update_board(access_token, board_id, title, content)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
        board_id: int,
        access_token: str = Depends(get_access_token),
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.delete_board(access_token, board_id)