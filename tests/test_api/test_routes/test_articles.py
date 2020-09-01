import pytest
from asyncpg.pool import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from app.db.errors import EntityDoesNotExist
from app.db.repositories.articles import ArticlesRepository
from app.db.repositories.profiles import ProfilesRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.articles import Article
from app.models.domain.users import UserInDB
from app.models.schemas.articles import ArticleInResponse, ListOfArticlesInResponse

pytestmark = pytest.mark.asyncio


async def test_user_can_not_create_article_with_duplicated_slug(
    app: FastAPI, authorized_client: AsyncClient, test_article: Article
) -> None:
    article_data = {
        "title": "Test Slug",
        "body": "does not matter",
        "description": "¯\\_(ツ)_/¯",
    }
    response = await authorized_client.post(
        app.url_path_for("articles:create-article"), json={"article": article_data}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_user_can_create_article(
    app: FastAPI, authorized_client: AsyncClient, test_user: UserInDB
) -> None:
    article_data = {
        "title": "Test Slug",
        "body": "does not matter",
        "description": "¯\\_(ツ)_/¯",
    }
    response = await authorized_client.post(
        app.url_path_for("articles:create-article"), json={"article": article_data}
    )
    article = ArticleInResponse(**response.json())
    assert article.article.title == article_data["title"]
    assert article.article.author.username == test_user.username


async def test_not_existing_tags_will_be_created_without_duplication(
    app: FastAPI, authorized_client: AsyncClient, test_user: UserInDB
) -> None:
    article_data = {
        "title": "Test Slug",
        "body": "does not matter",
        "description": "¯\\_(ツ)_/¯",
        "tagList": ["tag1", "tag2", "tag3", "tag3"],
    }
    response = await authorized_client.post(
        app.url_path_for("articles:create-article"), json={"article": article_data}
    )
    article = ArticleInResponse(**response.json())
    assert set(article.article.tags) == {"tag1", "tag2", "tag3"}


@pytest.mark.parametrize(
    "api_method, route_name",
    (("GET", "articles:get-article"), ("PUT", "articles:update-article")),
)
async def test_user_can_not_retrieve_not_existing_article(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    api_method: str,
    route_name: str,
) -> None:
    response = await authorized_client.request(
        api_method, app.url_path_for(route_name, slug="wrong-slug")
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_user_can_retrieve_article_if_exists(
    app: FastAPI, authorized_client: AsyncClient, test_article: Article
) -> None:
    response = await authorized_client.get(
        app.url_path_for("articles:get-article", slug=test_article.slug)
    )
    article = ArticleInResponse(**response.json())
    assert article.article == test_article


@pytest.mark.parametrize(
    "update_field, update_value, extra_updates",
    (
        ("title", "New Title", {"slug": "new-title"}),
        ("description", "new description", {}),
        ("body", "new body", {}),
    ),
)
async def test_user_can_update_article(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    update_field: str,
    update_value: str,
    extra_updates: dict,
) -> None:
    response = await authorized_client.put(
        app.url_path_for("articles:update-article", slug=test_article.slug),
        json={"article": {update_field: update_value}},
    )

    assert response.status_code == status.HTTP_200_OK

    article = ArticleInResponse(**response.json()).article
    article_as_dict = article.dict()
    assert article_as_dict[update_field] == update_value

    for extra_field, extra_value in extra_updates.items():
        assert article_as_dict[extra_field] == extra_value

    exclude_fields = {update_field, *extra_updates.keys(), "updated_at"}
    assert article.dict(exclude=exclude_fields) == test_article.dict(
        exclude=exclude_fields
    )


@pytest.mark.parametrize(
    "api_method, route_name",
    (("PUT", "articles:update-article"), ("DELETE", "articles:delete-article")),
)
async def test_user_can_not_modify_article_that_is_not_authored_by_him(
    app: FastAPI,
    authorized_client: AsyncClient,
    pool: Pool,
    api_method: str,
    route_name: str,
) -> None:
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        user = await users_repo.create_user(
            username="test_author", email="author@email.com", password="password"
        )
        articles_repo = ArticlesRepository(connection)
        await articles_repo.create_article(
            slug="test-slug",
            title="Test Slug",
            description="Slug for tests",
            body="Test " * 100,
            author=user,
            tags=["tests", "testing", "pytest"],
        )

    response = await authorized_client.request(
        api_method,
        app.url_path_for(route_name, slug="test-slug"),
        json={"article": {"title": "Updated Title"}},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_user_can_delete_his_article(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    pool: Pool,
) -> None:
    await authorized_client.delete(
        app.url_path_for("articles:delete-article", slug=test_article.slug)
    )

    async with pool.acquire() as connection:
        articles_repo = ArticlesRepository(connection)
        with pytest.raises(EntityDoesNotExist):
            await articles_repo.get_article_by_slug(slug=test_article.slug)


@pytest.mark.parametrize(
    "api_method, route_name, favorite_state",
    (
        ("POST", "articles:mark-article-favorite", True),
        ("DELETE", "articles:unmark-article-favorite", False),
    ),
)
async def test_user_can_change_favorite_state(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    test_user: UserInDB,
    pool: Pool,
    api_method: str,
    route_name: str,
    favorite_state: bool,
) -> None:
    if not favorite_state:
        async with pool.acquire() as connection:
            articles_repo = ArticlesRepository(connection)
            await articles_repo.add_article_into_favorites(
                article=test_article, user=test_user
            )

    await authorized_client.request(
        api_method, app.url_path_for(route_name, slug=test_article.slug)
    )

    response = await authorized_client.get(
        app.url_path_for("articles:get-article", slug=test_article.slug)
    )

    article = ArticleInResponse(**response.json())

    assert article.article.favorited == favorite_state
    assert article.article.favorites_count == int(favorite_state)


@pytest.mark.parametrize(
    "api_method, route_name, favorite_state",
    (
        ("POST", "articles:mark-article-favorite", True),
        ("DELETE", "articles:unmark-article-favorite", False),
    ),
)
async def test_user_can_not_change_article_state_twice(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    test_user: UserInDB,
    pool: Pool,
    api_method: str,
    route_name: str,
    favorite_state: bool,
) -> None:
    if favorite_state:
        async with pool.acquire() as connection:
            articles_repo = ArticlesRepository(connection)
            await articles_repo.add_article_into_favorites(
                article=test_article, user=test_user
            )

    response = await authorized_client.request(
        api_method, app.url_path_for(route_name, slug=test_article.slug)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_empty_feed_if_user_has_not_followings(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    test_user: UserInDB,
    pool: Pool,
) -> None:
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        articles_repo = ArticlesRepository(connection)

        for i in range(5):
            user = await users_repo.create_user(
                username=f"user-{i}", email=f"user-{i}@email.com", password="password"
            )
            for j in range(5):
                await articles_repo.create_article(
                    slug=f"slug-{i}-{j}",
                    title="tmp",
                    description="tmp",
                    body="tmp",
                    author=user,
                    tags=[f"tag-{i}-{j}"],
                )

    response = await authorized_client.get(
        app.url_path_for("articles:get-user-feed-articles")
    )

    articles = ListOfArticlesInResponse(**response.json())
    assert articles.articles == []


async def test_user_will_receive_only_following_articles(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    test_user: UserInDB,
    pool: Pool,
) -> None:
    following_author_username = "user-2"
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        profiles_repo = ProfilesRepository(connection)
        articles_repo = ArticlesRepository(connection)

        for i in range(5):
            user = await users_repo.create_user(
                username=f"user-{i}", email=f"user-{i}@email.com", password="password"
            )
            if i == 2:
                await profiles_repo.add_user_into_followers(
                    target_user=user, requested_user=test_user
                )

            for j in range(5):
                await articles_repo.create_article(
                    slug=f"slug-{i}-{j}",
                    title="tmp",
                    description="tmp",
                    body="tmp",
                    author=user,
                    tags=[f"tag-{i}-{j}"],
                )

    response = await authorized_client.get(
        app.url_path_for("articles:get-user-feed-articles")
    )

    articles_from_response = ListOfArticlesInResponse(**response.json())
    assert len(articles_from_response.articles) == 5

    all_from_following = (
        article.author.username == following_author_username
        for article in articles_from_response.articles
    )
    assert all(all_from_following)


async def test_user_receiving_feed_with_limit_and_offset(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_article: Article,
    test_user: UserInDB,
    pool: Pool,
) -> None:
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        profiles_repo = ProfilesRepository(connection)
        articles_repo = ArticlesRepository(connection)

        for i in range(5):
            user = await users_repo.create_user(
                username=f"user-{i}", email=f"user-{i}@email.com", password="password"
            )
            if i == 2:
                await profiles_repo.add_user_into_followers(
                    target_user=user, requested_user=test_user
                )

            for j in range(5):
                await articles_repo.create_article(
                    slug=f"slug-{i}-{j}",
                    title="tmp",
                    description="tmp",
                    body="tmp",
                    author=user,
                    tags=[f"tag-{i}-{j}"],
                )

    full_response = await authorized_client.get(
        app.url_path_for("articles:get-user-feed-articles")
    )
    full_articles = ListOfArticlesInResponse(**full_response.json())

    response = await authorized_client.get(
        app.url_path_for("articles:get-user-feed-articles"),
        params={"limit": 2, "offset": 3},
    )

    articles_from_response = ListOfArticlesInResponse(**response.json())
    assert full_articles.articles[3:] == articles_from_response.articles


async def test_article_will_contain_only_attached_tags(
    app: FastAPI, authorized_client: AsyncClient, test_user: UserInDB, pool: Pool
) -> None:
    attached_tags = ["tag1", "tag3"]

    async with pool.acquire() as connection:
        articles_repo = ArticlesRepository(connection)

        await articles_repo.create_article(
            slug=f"test-slug",
            title="tmp",
            description="tmp",
            body="tmp",
            author=test_user,
            tags=attached_tags,
        )

        for i in range(5):
            await articles_repo.create_article(
                slug=f"slug-{i}",
                title="tmp",
                description="tmp",
                body="tmp",
                author=test_user,
                tags=[f"tag-{i}"],
            )

    response = await authorized_client.get(
        app.url_path_for("articles:get-article", slug="test-slug")
    )
    article = ArticleInResponse(**response.json())
    assert len(article.article.tags) == len(attached_tags)
    assert set(article.article.tags) == set(attached_tags)


@pytest.mark.parametrize(
    "tag, result", (("", 7), ("tag1", 1), ("tag2", 2), ("wrong", 0))
)
async def test_filtering_by_tags(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_user: UserInDB,
    pool: Pool,
    tag: str,
    result: int,
) -> None:
    async with pool.acquire() as connection:
        articles_repo = ArticlesRepository(connection)

        await articles_repo.create_article(
            slug=f"slug-1",
            title="tmp",
            description="tmp",
            body="tmp",
            author=test_user,
            tags=["tag1", "tag2"],
        )
        await articles_repo.create_article(
            slug=f"slug-2",
            title="tmp",
            description="tmp",
            body="tmp",
            author=test_user,
            tags=["tag2"],
        )

        for i in range(5, 10):
            await articles_repo.create_article(
                slug=f"slug-{i}",
                title="tmp",
                description="tmp",
                body="tmp",
                author=test_user,
                tags=[f"tag-{i}"],
            )

    response = await authorized_client.get(
        app.url_path_for("articles:list-articles"), params={"tag": tag}
    )
    articles = ListOfArticlesInResponse(**response.json())
    assert articles.articles_count == result


@pytest.mark.parametrize(
    "author, result", (("", 8), ("author1", 1), ("author2", 2), ("wrong", 0))
)
async def test_filtering_by_authors(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_user: UserInDB,
    pool: Pool,
    author: str,
    result: int,
) -> None:
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        articles_repo = ArticlesRepository(connection)

        author1 = await users_repo.create_user(
            username="author1", email="author1@email.com", password="password"
        )
        author2 = await users_repo.create_user(
            username="author2", email="author2@email.com", password="password"
        )

        await articles_repo.create_article(
            slug=f"slug-1", title="tmp", description="tmp", body="tmp", author=author1
        )
        await articles_repo.create_article(
            slug=f"slug-2-1", title="tmp", description="tmp", body="tmp", author=author2
        )
        await articles_repo.create_article(
            slug=f"slug-2-2", title="tmp", description="tmp", body="tmp", author=author2
        )

        for i in range(5, 10):
            await articles_repo.create_article(
                slug=f"slug-{i}",
                title="tmp",
                description="tmp",
                body="tmp",
                author=test_user,
            )

    response = await authorized_client.get(
        app.url_path_for("articles:list-articles"), params={"author": author}
    )
    articles = ListOfArticlesInResponse(**response.json())
    assert articles.articles_count == result


@pytest.mark.parametrize(
    "favorited, result", (("", 7), ("fan1", 1), ("fan2", 2), ("wrong", 0))
)
async def test_filtering_by_favorited(
    app: FastAPI,
    authorized_client: AsyncClient,
    test_user: UserInDB,
    pool: Pool,
    favorited: str,
    result: int,
) -> None:
    async with pool.acquire() as connection:
        users_repo = UsersRepository(connection)
        articles_repo = ArticlesRepository(connection)

        fan1 = await users_repo.create_user(
            username="fan1", email="fan1@email.com", password="password"
        )
        fan2 = await users_repo.create_user(
            username="fan2", email="fan2@email.com", password="password"
        )

        article1 = await articles_repo.create_article(
            slug=f"slug-1", title="tmp", description="tmp", body="tmp", author=test_user
        )
        article2 = await articles_repo.create_article(
            slug=f"slug-2", title="tmp", description="tmp", body="tmp", author=test_user
        )

        await articles_repo.add_article_into_favorites(article=article1, user=fan1)
        await articles_repo.add_article_into_favorites(article=article1, user=fan2)
        await articles_repo.add_article_into_favorites(article=article2, user=fan2)

        for i in range(5, 10):
            await articles_repo.create_article(
                slug=f"slug-{i}",
                title="tmp",
                description="tmp",
                body="tmp",
                author=test_user,
            )

    response = await authorized_client.get(
        app.url_path_for("articles:list-articles"), params={"favorited": favorited}
    )
    articles = ListOfArticlesInResponse(**response.json())
    assert articles.articles_count == result


async def test_filtering_with_limit_and_offset(
    app: FastAPI, authorized_client: AsyncClient, test_user: UserInDB, pool: Pool
) -> None:
    async with pool.acquire() as connection:
        articles_repo = ArticlesRepository(connection)

        for i in range(5, 10):
            await articles_repo.create_article(
                slug=f"slug-{i}",
                title="tmp",
                description="tmp",
                body="tmp",
                author=test_user,
            )

    full_response = await authorized_client.get(
        app.url_path_for("articles:list-articles")
    )
    full_articles = ListOfArticlesInResponse(**full_response.json())

    response = await authorized_client.get(
        app.url_path_for("articles:list-articles"), params={"limit": 2, "offset": 3}
    )

    articles_from_response = ListOfArticlesInResponse(**response.json())
    assert full_articles.articles[3:] == articles_from_response.articles
