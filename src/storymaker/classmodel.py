from pydantic import BaseModel, Field, ConfigDict


class NovelFrontmatter(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    title: str = Field(description="title of this novel in Japanese.")
    author: str = Field(
        description="""author of this novel. 
        Please think of this novel's author pen name in Japanese randomly.
        Pen name must not be a real name or a name of a famous author.
        """
    )
    synopsis: str = Field(
        description="""attractive synopsis of this novel in Japanese.
        synopsis is used to describe the story of this novel.
        synopsis length must be 100 to 200 words.
        """
    )
    tags: list[str] = Field(
        description="""
        tags of this novel in Japanese. 
        tag is used to describe the genre or key motif or both of this novel. 
        tags length must be 2 to 4.
        """
    )


if __name__ == "__main__":
    print(NovelFrontmatter.model_json_schema())
