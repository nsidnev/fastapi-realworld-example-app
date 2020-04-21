-- name: add-article-to-favorites!
INSERT INTO favorites (user_id, article_id)
VALUES ((SELECT id FROM users WHERE username = :username),
        (SELECT id FROM articles WHERE slug = :slug))
ON CONFLICT DO NOTHING;


-- name: remove-article-from-favorites!
DELETE
FROM favorites
WHERE user_id = (SELECT id FROM users WHERE username = :username)
  AND article_id = (SELECT id FROM articles WHERE slug = :slug);


-- name: is-article-in-favorites^
SELECT CASE WHEN count(user_id) > 0 THEN TRUE ELSE FALSE END AS favorited
FROM favorites
WHERE user_id = (SELECT id FROM users WHERE username = :username)
  AND article_id = (SELECT id FROM articles WHERE slug = :slug);


-- name: get-favorites-count-for-article^
SELECT count(*) as favorites_count
FROM favorites
WHERE article_id = (SELECT id FROM articles WHERE slug = :slug);


-- name: get-tags-for-article-by-slug
SELECT t.tag
FROM tags t
         INNER JOIN articles_to_tags att ON
        t.tag = att.tag
        AND
        att.article_id = (SELECT id FROM articles WHERE slug = :slug);


-- name: get-article-by-slug^
SELECT id,
       slug,
       title,
       description,
       body,
       created_at,
       updated_at,
       (SELECT username FROM users WHERE id = author_id) AS author_username
FROM articles
WHERE slug = :slug
LIMIT 1;


-- name: create-new-article<!
WITH author_subquery AS (
    SELECT id, username
    FROM users
    WHERE username = :author_username
)
INSERT
INTO articles (slug, title, description, body, author_id)
VALUES (:slug, :title, :description, :body, (SELECT id FROM author_subquery))
RETURNING
    id,
    slug,
    title,
    description,
    body,
        (SELECT username FROM author_subquery) as author_username,
    created_at,
    updated_at;


-- name: add-tags-to-article*!
INSERT INTO articles_to_tags (article_id, tag)
VALUES ((SELECT id FROM articles WHERE slug = :slug),
        (SELECT tag FROM tags WHERE tag = :tag))
ON CONFLICT DO NOTHING;


-- name: update-article<!
UPDATE articles
SET slug        = :new_slug,
    title       = :new_title,
    body        = :new_body,
    description = :new_description
WHERE slug = :slug
  AND author_id = (SELECT id FROM users WHERE username = :author_username)
RETURNING updated_at;


-- name: delete-article!
DELETE
FROM articles
WHERE slug = :slug
  AND author_id = (SELECT id FROM users WHERE username = :author_username);


-- name: get-articles-for-feed
SELECT a.id,
       a.slug,
       a.title,
       a.description,
       a.body,
       a.created_at,
       a.updated_at,
       (
           SELECT username
           FROM users
           WHERE id = a.author_id
       ) AS author_username
FROM articles a
         INNER JOIN followers_to_followings f ON
        f.following_id = a.author_id AND
        f.follower_id = (SELECT id FROM users WHERE username = :follower_username)
ORDER BY a.created_at
LIMIT :limit
OFFSET
:offset;
