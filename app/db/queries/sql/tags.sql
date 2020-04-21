-- name: get-all-tags
SELECT tag
FROM tags;


-- name: create-new-tags*!
INSERT INTO tags (tag)
VALUES (:tag)
ON CONFLICT DO NOTHING;
