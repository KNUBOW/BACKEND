from fastapi import APIRouter, Form, UploadFile, Depends, Query

from core.di import get_board_service
from service.board_service import BoardService

router = APIRouter(prefix="/board", tags=["Board"])

@router.get("/list", status_code=200)
async def get_all_boards(   # 검색 및 게시글 list 확인
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1),
        title: str | None = None,
        nickname: str | None = None,
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.get_all_boards(skip=skip, limit=limit, title=title, nickname=nickname)
@router.post("", status_code=201)
async def create_board(
        title: str = Form(...),
        content: str = Form(...),
        images: list[UploadFile] = [],
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.create_board(title, content, images)

@router.get("/{board_id}", status_code=200)
async def get_board(
        board_id: int,
        board_service: BoardService = Depends(get_board_service)
):
    return await board_service.get_board(board_id)

@router.delete("/{board_id}", status_code=204)
async def delete_board(
        board_id: int,
        board_service: BoardService = Depends(get_board_service)
):
    await board_service.soft_delete_board(board_id)

@router.post("/{board_id}/like", status_code=201)
async def like_board(
    board_id: int,
    board_service: BoardService = Depends(get_board_service)
):
    return await board_service.like_board(board_id)

@router.post("/{board_id}/comment", status_code=201)
async def create_comment(
    board_id: int,
    comment: str = Form(...),
    board_service: BoardService = Depends(get_board_service)
):
    return await board_service.create_comment(board_id, comment)

@router.get("/{board_id}/comments", status_code=200)
async def get_comments(
    board_id: int,
    board_service: BoardService = Depends(get_board_service)
):
    return await board_service.get_comments(board_id)

@router.delete("/comment/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: int,
    board_service: BoardService = Depends(get_board_service)
):
    await board_service.delete_comment(comment_id)
