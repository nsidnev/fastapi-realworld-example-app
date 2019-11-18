# API messages

USER_DOES_NOT_EXIST_ERROR = "user does not exist"
ARTICLE_DOES_NOT_EXIST_ERROR = "article does not exist"
ARTICLE_ALREADY_EXISTS_ERROR = "article already exists"
USER_IS_NOT_AUTHOR_OF_ARTICLE = "you are not an author of this article"

INCORRECT_LOGIN_INPUT_ERROR = "incorrect email or password"
USERNAME_TAKEN_ERROR = "user with this username already exists"
EMAIL_TAKEN_ERROR = "user with this email already exists"

UNABLE_TO_FOLLOW_YOURSELF_ERROR = "user can not follow him self"
UNABLE_TO_UNSUBSCRIBE_FROM_YOURSELF_ERROR = "user can not unsubscribe from him self"
USER_IS_NOT_FOLLOWED_ERROR = "you don't follow this user"
USER_IS_ALREADY_FOLLOWED_ERROR = "you follow this user already"

WRONG_TOKEN_PREFIX_ERROR = "unsupported authorization type"  # noqa: S105
MALFORMED_PAYLOAD_ERROR = "could not validate credentials"

ARTICLE_IS_ALREADY_FAVORITED = "you are already marked this articles as favorite"
ARTICLE_IS_NOT_FAVORITED = "article is not favorited"

COMMENT_DOES_NOT_EXIST_ERROR = "comment does not exist"
