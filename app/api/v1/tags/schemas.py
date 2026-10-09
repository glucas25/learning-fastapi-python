from pydantic import BaseModel, ConfigDict, Field

class TagPublic(BaseModel):
    id: int
    name: str = Field(...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta",
        examples=["Python"])

    model_config=ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    name:str = Field(...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta",
        examples=["Python"]
    )

class TagUpdate(BaseModel):
    name:str = Field(...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta",
        examples=["Python"]
    )

class TagWithCount(TagPublic):
    uses: int