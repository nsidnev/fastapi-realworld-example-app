import pytest
from asyncpg.pool import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from app.db.repositories.comments import CommentsRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.articles import Article
from app.models.schemas.comments import CommentInResponse, ListOfCommentsInResponse

pytestmark = pytest.mark.asyncio


async def test_user_can_add_comment_for_article(
    app: FastAPI, authorized_client: AsyncClient, test_article: Article
) -> None:
    created_comment_response = await authorized_client.post(
        app.url_path_for("comments:create-comment-for-article", slug=test_article.slug),
        json={"comment": {"body": "comment"}},
    )

    created_comment = CommentInResponse(**created_comment_response.json())

    comments_for_article_response = await authorized_client.get(
        app.url_path_for("comments:get-comments-for-article", slug=test_article.slug)
    )

    comments = ListOfCommentsInResponse(**comments_for_article_response.json())

    assert created_comment.comment == comments.comments[0]


async def test_user_can_delete_own_comment(
    app: FastAPI, authorized_client: AsyncClient, test_article: Article
) -> None:
    created_comment_response = await authorized_client.post(
        app.url_path_for("comments:create-comment-for-article", slug=test_article.slug),
        json={"comment": {"body": "comment"}},
    )

    created_comment = CommentInResponse(**created_comment_response.json())

    await authorized_client.delete(
        app.url_path_for(
            "comments:delete-comment-from-article",
            slug=test_article.slug,
            comment_id=str(created_comment.comment.id_),
        )
    )

    comments_for_article_response = await authorized_client.get(
        app.url_path_for("comments:get-comments-for-article", slug=test_article.slug)
    )

    comments = ListOfCommentsInResponse(**comments_for_article_response.json())

    assert len(comments.comments) == 0


async def test_user_can_not_delete_not_authored_comment(
    app: FastAPI, authorized_client: AsyncClient, test_article: Article, pool: Pool
) -> None:
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        user = await users_repo.create_user(
            username="test_author", email="author@email.com", password="password"
        )
        comments_repo = CommentsRepository(connection)
        comment = await comments_repo.create_comment_for_article(
            body="tmp", article=test_article, user=user
        )

    forbidden_response = await authorized_client.delete(
        app.url_path_for(
            "comments:delete-comment-from-article",
            slug=test_article.slug,
            comment_id=str(comment.id_),
        )
    )

    assert forbidden_response.status_code == status.HTTP_403_FORBIDDEN


async def test_user_will_receive_error_for_not_existing_comment(
    app: FastAPI, authorized_client: AsyncClient, test_article: Article
) -> None:
    not_found_response = await authorized_client.delete(
        app.url_path_for(
            "comments:delete-comment-from-article",
            slug=test_article.slug,
            comment_id="1",
        )
    )

    assert not_found_response.status_code == status.HTTP_404_NOT_FOUND
