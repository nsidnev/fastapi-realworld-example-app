-- name: get-comments-for-article-by-slug
SELECT c.id,
       c.body,
       c.created_at,
       c.updated_at,
       (SELECT username FROM users WHERE id = c.author_id) as author_username
FROM commentaries c
         INNER JOIN articles a ON c.article_id = a.id AND (a.slug = :slug);

-- name: get-comment-by-id-and-slug^
SELECT c.id,
       c.body,
       c.created_at,
       c.updated_at,
       (SELECT username FROM users WHERE id = c.author_id) as author_username
FROM commentaries c
         INNER JOIN articles a ON c.article_id = a.id AND (a.slug = :article_slug)
WHERE c.id = :comment_id;

-- name: create-new-comment<!
WITH users_subquery AS (
        (SELECT id, username FROM users WHERE username = :author_username)
)
INSERT
INTO commentaries (body, author_id, article_id)
VALUES (:body,
        (SELECT id FROM users_subquery),
        (SELECT id FROM articles WHERE slug = :article_slug))
RETURNING
    id,
    body,
        (SELECT username FROM users_subquery) AS author_username,
    created_at,
    updated_at;

-- name: delete-comment-by-id!
DELETE
FROM commentaries
WHERE id = :comment_id
  AND author_id = (SELECT id FROM users WHERE username = :author_username);
