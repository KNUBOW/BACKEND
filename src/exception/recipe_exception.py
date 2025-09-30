from exception.base_exception import CustomException

class RecipeNotFoundException(CustomException):
    def __init__(self, detail="해당 레시피가 존재하지 않아 삭제할 수 없습니다"):
        super().__init__(status_code=404, detail=detail, code="RECIPE_NOT_FOUND")
