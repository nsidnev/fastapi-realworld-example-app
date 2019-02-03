"""init

Revision ID: 4e62e0d755a8
Revises: 
Create Date: 2019-01-27 16:47:58.791783

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4e62e0d755a8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        CREATE FUNCTION update_updated_at_column() 
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW; 
        END;
        $$ language 'plpgsql';
        
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            salt VARCHAR(255) NULL,
            hashed_password VARCHAR(255) NULL,
            bio VARCHAR(500) NULL,
            image VARCHAR(255) NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        );
        CREATE TRIGGER update_user_modtime 
        BEFORE UPDATE ON users 
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
        
        CREATE TABLE followers (
            id SERIAL PRIMARY KEY,
            follower_id INTEGER,
            following_id INTEGER,
            UNIQUE(follower_id, following_id),
            FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (following_id) REFERENCES users (id) ON DELETE CASCADE
        );
        
        CREATE TABLE articles (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(255) NOT NULL UNIQUE,
            title VARCHAR(255) NOT NULL,
            description VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            author_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE SET NULL
        );
        CREATE TRIGGER update_article_modtime 
        BEFORE UPDATE ON articles 
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
        
        CREATE TABLE tags (
            id SERIAL PRIMARY KEY,
            tag VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        );
        CREATE TRIGGER update_tag_modtime 
        BEFORE UPDATE ON tags 
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
        
        CREATE TABLE article_tags (
            id SERIAL PRIMARY KEY,
            article_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE 
        );
        
        CREATE TABLE favourites (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            article_id INTEGER,
            UNIQUE(user_id, article_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE
        );
        
        CREATE TABLE commentaries (
            id SERIAL PRIMARY KEY,
            body TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            author_id INTEGER,
            article_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE 
        );
        CREATE TRIGGER update_comment_modtime
        BEFORE UPDATE ON commentaries 
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        """
            DROP TRIGGER update_comment_modtime ON commentaries;
            DROP TABLE commentaries;
            DROP TABLE favourites;
            DROP TABLE article_tags;
            DROP TRIGGER update_tag_modtime ON tags;
            DROP TABLE tags;
            DROP TRIGGER update_article_modtime ON articles;
            DROP TABLE articles;
            DROP TABLE followers;
            DROP TRIGGER update_user_modtime ON users;
            DROP TABLE users;
            DROP FUNCTION update_updated_at_column;
        """
    )
