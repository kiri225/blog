-- 博客 PostgreSQL 建表脚本（含中文备注）
-- 目标库: blog
-- 执行: 用项目脚本或 psql -d blog -f init_db.sql

-- ============================================
-- 1. User（用户/管理员）
-- ============================================
CREATE TABLE IF NOT EXISTS "user" (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50)  UNIQUE NOT NULL,
    hashed_password VARCHAR(128) NOT NULL,
    nickname        VARCHAR(50)  DEFAULT '',
    avatar          VARCHAR(500) DEFAULT '',
    email           VARCHAR(100) DEFAULT '',
    bio             VARCHAR(500) DEFAULT '',
    is_admin        BOOLEAN      DEFAULT FALSE,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE "user" IS '用户/管理员';
COMMENT ON COLUMN "user".id IS '主键';
COMMENT ON COLUMN "user".username IS '登录用户名';
COMMENT ON COLUMN "user".hashed_password IS '密码哈希';
COMMENT ON COLUMN "user".nickname IS '昵称';
COMMENT ON COLUMN "user".avatar IS '头像 URL';
COMMENT ON COLUMN "user".email IS '邮箱';
COMMENT ON COLUMN "user".bio IS '个人简介';
COMMENT ON COLUMN "user".is_admin IS '是否管理员';
COMMENT ON COLUMN "user".created_at IS '创建时间';
COMMENT ON COLUMN "user".updated_at IS '更新时间';

-- ============================================
-- 2. Category（分类）
-- ============================================
CREATE TABLE IF NOT EXISTS category (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(50)  UNIQUE NOT NULL,
    slug          VARCHAR(50)  UNIQUE NOT NULL,
    description   VARCHAR(200) DEFAULT '',
    sort          INTEGER      DEFAULT 0,
    post_count    INTEGER      DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE category IS '文章分类';
COMMENT ON COLUMN category.id IS '主键';
COMMENT ON COLUMN category.name IS '分类名称';
COMMENT ON COLUMN category.slug IS 'URL 别名';
COMMENT ON COLUMN category.description IS '分类描述';
COMMENT ON COLUMN category.sort IS '排序，越小越靠前';
COMMENT ON COLUMN category.post_count IS '文章数量';
COMMENT ON COLUMN category.created_at IS '创建时间';
COMMENT ON COLUMN category.updated_at IS '更新时间';

-- ============================================
-- 3. Tag（标签）
-- ============================================
CREATE TABLE IF NOT EXISTS tag (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(50)  UNIQUE NOT NULL,
    slug          VARCHAR(50)  UNIQUE NOT NULL,
    post_count    INTEGER      DEFAULT 0
);

COMMENT ON TABLE tag IS '文章标签';
COMMENT ON COLUMN tag.id IS '主键';
COMMENT ON COLUMN tag.name IS '标签名称';
COMMENT ON COLUMN tag.slug IS 'URL 别名';
COMMENT ON COLUMN tag.post_count IS '文章数量';

-- ============================================
-- 4. Post（文章）
-- ============================================
CREATE TABLE IF NOT EXISTS post (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    slug          VARCHAR(200) UNIQUE NOT NULL,
    description   VARCHAR(500) DEFAULT '',
    content       TEXT         DEFAULT '',
    cover         VARCHAR(500) DEFAULT '',
    category_id   INTEGER      REFERENCES category(id) ON DELETE SET NULL,
    status        VARCHAR(20)  DEFAULT 'draft',
    is_pinned     BOOLEAN      DEFAULT FALSE,
    views         INTEGER      DEFAULT 0,
    likes         INTEGER      DEFAULT 0,
    word_count    INTEGER      DEFAULT 0,
    reading_time  INTEGER      DEFAULT 0,
    published_at  TIMESTAMP,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_slug ON post(slug);
CREATE INDEX IF NOT EXISTS idx_post_status ON post(status);
CREATE INDEX IF NOT EXISTS idx_post_category ON post(category_id);

COMMENT ON TABLE post IS '文章';
COMMENT ON COLUMN post.id IS '主键';
COMMENT ON COLUMN post.title IS '标题';
COMMENT ON COLUMN post.slug IS 'URL 别名';
COMMENT ON COLUMN post.description IS '摘要';
COMMENT ON COLUMN post.content IS '正文';
COMMENT ON COLUMN post.cover IS '封面图 URL';
COMMENT ON COLUMN post.category_id IS '所属分类';
COMMENT ON COLUMN post.status IS '状态：draft / published / archived';
COMMENT ON COLUMN post.is_pinned IS '是否置顶';
COMMENT ON COLUMN post.views IS '浏览量';
COMMENT ON COLUMN post.likes IS '点赞数';
COMMENT ON COLUMN post.word_count IS '字数';
COMMENT ON COLUMN post.reading_time IS '预计阅读分钟数';
COMMENT ON COLUMN post.published_at IS '发布时间';
COMMENT ON COLUMN post.created_at IS '创建时间';
COMMENT ON COLUMN post.updated_at IS '更新时间';

-- ============================================
-- 5. PostTag（文章-标签 中间表）
-- ============================================
CREATE TABLE IF NOT EXISTS post_tag (
    post_id       INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    tag_id        INTEGER NOT NULL REFERENCES tag(id)  ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

COMMENT ON TABLE post_tag IS '文章与标签多对多关联';
COMMENT ON COLUMN post_tag.post_id IS '文章 ID';
COMMENT ON COLUMN post_tag.tag_id IS '标签 ID';

-- ============================================
-- 6. GitHubUser（GitHub 登录用户）
-- ============================================
CREATE TABLE IF NOT EXISTS github_user (
    id            SERIAL PRIMARY KEY,
    github_id     INTEGER      UNIQUE NOT NULL,
    login         VARCHAR(100) NOT NULL,
    avatar        VARCHAR(500) DEFAULT '',
    bio           VARCHAR(500) DEFAULT '',
    created_at    TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_github_user_id ON github_user(github_id);

COMMENT ON TABLE github_user IS 'GitHub 登录用户';
COMMENT ON COLUMN github_user.id IS '主键';
COMMENT ON COLUMN github_user.github_id IS 'GitHub 用户数字 ID';
COMMENT ON COLUMN github_user.login IS 'GitHub 登录名';
COMMENT ON COLUMN github_user.avatar IS '头像 URL';
COMMENT ON COLUMN github_user.bio IS '简介';
COMMENT ON COLUMN github_user.created_at IS '创建时间';

-- ============================================
-- 7. Comment（文章评论）
-- ============================================
CREATE TABLE IF NOT EXISTS comment (
    id              SERIAL PRIMARY KEY,
    post_id         INTEGER      NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    parent_id       INTEGER      REFERENCES comment(id) ON DELETE CASCADE,
    github_user_id  INTEGER      REFERENCES github_user(id) ON DELETE SET NULL,
    content         TEXT         NOT NULL,
    likes           INTEGER      DEFAULT 0,
    ip              VARCHAR(45)  DEFAULT '',
    status          VARCHAR(20)  DEFAULT 'approved',
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comment_post ON comment(post_id);
CREATE INDEX IF NOT EXISTS idx_comment_status ON comment(status);
CREATE INDEX IF NOT EXISTS idx_comment_github_user ON comment(github_user_id);

COMMENT ON TABLE comment IS '文章评论（GitHub 登录）';
COMMENT ON COLUMN comment.id IS '主键';
COMMENT ON COLUMN comment.post_id IS '所属文章';
COMMENT ON COLUMN comment.parent_id IS '父评论，用于回复';
COMMENT ON COLUMN comment.github_user_id IS '评论者 GitHub 用户';
COMMENT ON COLUMN comment.content IS '评论内容';
COMMENT ON COLUMN comment.likes IS '点赞数';
COMMENT ON COLUMN comment.ip IS '评论者 IP';
COMMENT ON COLUMN comment.status IS '状态：pending / approved / rejected';
COMMENT ON COLUMN comment.created_at IS '创建时间';

-- ============================================
-- 8. Message（留言板）
-- ============================================
CREATE TABLE IF NOT EXISTS message (
    id              SERIAL PRIMARY KEY,
    github_user_id  INTEGER      REFERENCES github_user(id) ON DELETE SET NULL,
    parent_id       INTEGER      REFERENCES message(id) ON DELETE CASCADE,
    content         TEXT         NOT NULL,
    ip              VARCHAR(45)  DEFAULT '',
    status          VARCHAR(20)  DEFAULT 'approved',
    likes           INTEGER      DEFAULT 0,
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_message_status ON message(status);
CREATE INDEX IF NOT EXISTS idx_message_parent ON message(parent_id);
CREATE INDEX IF NOT EXISTS idx_message_github_user ON message(github_user_id);

COMMENT ON TABLE message IS '留言板/杂谈';
COMMENT ON COLUMN message.id IS '主键';
COMMENT ON COLUMN message.github_user_id IS '留言者 GitHub 用户';
COMMENT ON COLUMN message.parent_id IS '父留言，用于回复';
COMMENT ON COLUMN message.content IS '留言内容';
COMMENT ON COLUMN message.ip IS '留言者 IP';
COMMENT ON COLUMN message.status IS '状态：pending / approved / rejected';
COMMENT ON COLUMN message.likes IS '点赞数';
COMMENT ON COLUMN message.created_at IS '创建时间';

-- ============================================
-- 9. Chatter（说说）
-- ============================================
CREATE TABLE IF NOT EXISTS chatter (
    id              SERIAL PRIMARY KEY,
    content         TEXT         NOT NULL,
    images          TEXT         DEFAULT '[]',
    mood            VARCHAR(20)  DEFAULT '',
    likes           INTEGER      DEFAULT 0,
    comments_count  INTEGER      DEFAULT 0,
    status          VARCHAR(20)  DEFAULT 'draft',
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chatter_status ON chatter(status);

COMMENT ON TABLE chatter IS '说说/微语';
COMMENT ON COLUMN chatter.id IS '主键';
COMMENT ON COLUMN chatter.content IS '说说正文';
COMMENT ON COLUMN chatter.images IS '图片 JSON 数组';
COMMENT ON COLUMN chatter.mood IS '心情';
COMMENT ON COLUMN chatter.likes IS '点赞数';
COMMENT ON COLUMN chatter.comments_count IS '评论数';
COMMENT ON COLUMN chatter.status IS '状态：draft / published';
COMMENT ON COLUMN chatter.created_at IS '创建时间';
COMMENT ON COLUMN chatter.updated_at IS '更新时间';

-- ============================================
-- 10. ChatterComment（说说评论）
-- ============================================
CREATE TABLE IF NOT EXISTS chatter_comment (
    id              SERIAL PRIMARY KEY,
    chatter_id      INTEGER      NOT NULL REFERENCES chatter(id) ON DELETE CASCADE,
    parent_id       INTEGER      REFERENCES chatter_comment(id) ON DELETE CASCADE,
    github_user_id  INTEGER      REFERENCES github_user(id) ON DELETE SET NULL,
    content         TEXT         NOT NULL,
    ip              VARCHAR(45)  DEFAULT '',
    likes           INTEGER      DEFAULT 0,
    status          VARCHAR(20)  DEFAULT 'approved',
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chatter_comment_chatter ON chatter_comment(chatter_id);
CREATE INDEX IF NOT EXISTS idx_chatter_comment_status ON chatter_comment(status);
CREATE INDEX IF NOT EXISTS idx_chatter_comment_github_user ON chatter_comment(github_user_id);

COMMENT ON TABLE chatter_comment IS '说说评论（GitHub 登录）';
COMMENT ON COLUMN chatter_comment.id IS '主键';
COMMENT ON COLUMN chatter_comment.chatter_id IS '所属说说';
COMMENT ON COLUMN chatter_comment.parent_id IS '父评论，用于回复';
COMMENT ON COLUMN chatter_comment.github_user_id IS '评论者 GitHub 用户';
COMMENT ON COLUMN chatter_comment.content IS '评论内容';
COMMENT ON COLUMN chatter_comment.ip IS '评论者 IP';
COMMENT ON COLUMN chatter_comment.likes IS '点赞数';
COMMENT ON COLUMN chatter_comment.status IS '状态：pending / approved / rejected';
COMMENT ON COLUMN chatter_comment.created_at IS '创建时间';

-- ============================================
-- 11. Album（相册）
-- ============================================
CREATE TABLE IF NOT EXISTS album (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(100) NOT NULL,
    description   VARCHAR(500) DEFAULT '',
    cover         VARCHAR(500) DEFAULT '',
    photo_count   INTEGER      DEFAULT 0,
    sort          INTEGER      DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE album IS '相册';
COMMENT ON COLUMN album.id IS '主键';
COMMENT ON COLUMN album.title IS '相册标题';
COMMENT ON COLUMN album.description IS '相册描述';
COMMENT ON COLUMN album.cover IS '封面图 URL';
COMMENT ON COLUMN album.photo_count IS '照片数量';
COMMENT ON COLUMN album.sort IS '排序，越小越靠前';
COMMENT ON COLUMN album.created_at IS '创建时间';
COMMENT ON COLUMN album.updated_at IS '更新时间';

-- ============================================
-- 12. Photo（照片）
-- ============================================
CREATE TABLE IF NOT EXISTS photo (
    id            SERIAL PRIMARY KEY,
    album_id      INTEGER      NOT NULL REFERENCES album(id) ON DELETE CASCADE,
    url           VARCHAR(500) NOT NULL,
    caption       VARCHAR(200) DEFAULT '',
    orientation   VARCHAR(20)  DEFAULT 'landscape',
    sort          INTEGER      DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_photo_album ON photo(album_id);

COMMENT ON TABLE photo IS '相册照片';
COMMENT ON COLUMN photo.id IS '主键';
COMMENT ON COLUMN photo.album_id IS '所属相册';
COMMENT ON COLUMN photo.url IS '图片 URL';
COMMENT ON COLUMN photo.caption IS '照片说明';
COMMENT ON COLUMN photo.orientation IS '方向：landscape / portrait';
COMMENT ON COLUMN photo.sort IS '排序，越小越靠前';
COMMENT ON COLUMN photo.created_at IS '创建时间';

-- ============================================
-- 13. Project（项目展示）
-- ============================================
CREATE TABLE IF NOT EXISTS project (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    slug             VARCHAR(100) UNIQUE NOT NULL,
    description      VARCHAR(500) DEFAULT '',
    long_description TEXT         DEFAULT '',
    cover_image      VARCHAR(500) DEFAULT '',
    tech_stack       TEXT         DEFAULT '[]',
    link_github      VARCHAR(300) DEFAULT '',
    link_gitee       VARCHAR(300) DEFAULT '',
    link_live        VARCHAR(300) DEFAULT '',
    link_docs        VARCHAR(300) DEFAULT '',
    status           VARCHAR(20)  DEFAULT 'developing',
    status_label     VARCHAR(20)  DEFAULT '',
    is_featured      BOOLEAN      DEFAULT FALSE,
    sort             INTEGER      DEFAULT 0,
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE project IS '项目展示';
COMMENT ON COLUMN project.id IS '主键';
COMMENT ON COLUMN project.name IS '项目名称';
COMMENT ON COLUMN project.slug IS 'URL 别名';
COMMENT ON COLUMN project.description IS '短描述';
COMMENT ON COLUMN project.long_description IS '详细介绍';
COMMENT ON COLUMN project.cover_image IS '封面图 URL';
COMMENT ON COLUMN project.tech_stack IS '技术栈 JSON 数组';
COMMENT ON COLUMN project.link_github IS 'GitHub 地址';
COMMENT ON COLUMN project.link_gitee IS 'Gitee 地址';
COMMENT ON COLUMN project.link_live IS '线上预览地址';
COMMENT ON COLUMN project.link_docs IS '文档地址';
COMMENT ON COLUMN project.status IS '状态：developing / active / archived';
COMMENT ON COLUMN project.status_label IS '状态展示文案';
COMMENT ON COLUMN project.is_featured IS '是否精选';
COMMENT ON COLUMN project.sort IS '排序，越小越靠前';
COMMENT ON COLUMN project.created_at IS '创建时间';
COMMENT ON COLUMN project.updated_at IS '更新时间';

-- ============================================
-- 14. FriendLink（友情链接）
-- ============================================
CREATE TABLE IF NOT EXISTS friend_link (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    url           VARCHAR(300) NOT NULL,
    avatar        VARCHAR(500) DEFAULT '',
    description   VARCHAR(300) DEFAULT '',
    sort          INTEGER      DEFAULT 0,
    is_approved   BOOLEAN      DEFAULT FALSE,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE friend_link IS '友情链接';
COMMENT ON COLUMN friend_link.id IS '主键';
COMMENT ON COLUMN friend_link.name IS '站点名称';
COMMENT ON COLUMN friend_link.url IS '站点地址';
COMMENT ON COLUMN friend_link.avatar IS '头像/图标 URL';
COMMENT ON COLUMN friend_link.description IS '站点描述';
COMMENT ON COLUMN friend_link.sort IS '排序，越小越靠前';
COMMENT ON COLUMN friend_link.is_approved IS '是否通过审核（true 才在前台展示）';
COMMENT ON COLUMN friend_link.created_at IS '创建时间';
COMMENT ON COLUMN friend_link.updated_at IS '更新时间';

-- ============================================
-- 15. BookmarkCategory（收藏夹分类）
-- ============================================
CREATE TABLE IF NOT EXISTS bookmark_category (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(50)  NOT NULL,
    icon          VARCHAR(50)  DEFAULT '',
    description   VARCHAR(200) DEFAULT '',
    sort          INTEGER      DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE bookmark_category IS '收藏夹分类';
COMMENT ON COLUMN bookmark_category.id IS '主键';
COMMENT ON COLUMN bookmark_category.name IS '分类名称';
COMMENT ON COLUMN bookmark_category.icon IS '图标';
COMMENT ON COLUMN bookmark_category.description IS '分类描述';
COMMENT ON COLUMN bookmark_category.sort IS '排序，越小越靠前';
COMMENT ON COLUMN bookmark_category.created_at IS '创建时间';
COMMENT ON COLUMN bookmark_category.updated_at IS '更新时间';

-- ============================================
-- 16. BookmarkSite（收藏站点）
-- ============================================
CREATE TABLE IF NOT EXISTS bookmark_site (
    id            SERIAL PRIMARY KEY,
    category_id   INTEGER      NOT NULL REFERENCES bookmark_category(id) ON DELETE CASCADE,
    name          VARCHAR(100) NOT NULL,
    url           VARCHAR(300) NOT NULL,
    icon          VARCHAR(500) DEFAULT '',
    description   VARCHAR(300) DEFAULT '',
    platforms     TEXT         DEFAULT '[]',
    sort          INTEGER      DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bookmark_site_category ON bookmark_site(category_id);

COMMENT ON TABLE bookmark_site IS '收藏站点';
COMMENT ON COLUMN bookmark_site.id IS '主键';
COMMENT ON COLUMN bookmark_site.category_id IS '所属收藏分类';
COMMENT ON COLUMN bookmark_site.name IS '站点名称';
COMMENT ON COLUMN bookmark_site.url IS '站点地址';
COMMENT ON COLUMN bookmark_site.icon IS '图标 URL';
COMMENT ON COLUMN bookmark_site.description IS '站点描述';
COMMENT ON COLUMN bookmark_site.platforms IS '适用平台 JSON 数组';
COMMENT ON COLUMN bookmark_site.sort IS '排序，越小越靠前';
COMMENT ON COLUMN bookmark_site.created_at IS '创建时间';
COMMENT ON COLUMN bookmark_site.updated_at IS '更新时间';

-- ============================================
-- 17. SiteConfig（站点配置）
-- ============================================
CREATE TABLE IF NOT EXISTS site_config (
    id            SERIAL PRIMARY KEY,
    key           VARCHAR(100) UNIQUE NOT NULL,
    value         TEXT         DEFAULT '',
    description   VARCHAR(200) DEFAULT '',
    updated_at    TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE site_config IS '站点配置';
COMMENT ON COLUMN site_config.id IS '主键';
COMMENT ON COLUMN site_config.key IS '配置键';
COMMENT ON COLUMN site_config.value IS '配置值（JSON 字符串）';
COMMENT ON COLUMN site_config.description IS '配置说明';
COMMENT ON COLUMN site_config.updated_at IS '更新时间';

-- ============================================
-- 18. Visitor（访客记录）
-- ============================================
CREATE TABLE IF NOT EXISTS visitor (
    id            SERIAL PRIMARY KEY,
    ip            VARCHAR(45)  NOT NULL,
    path          VARCHAR(500) DEFAULT '',
    user_agent    TEXT         DEFAULT '',
    city          VARCHAR(100) DEFAULT '',
    region        VARCHAR(100) DEFAULT '',
    country       VARCHAR(100) DEFAULT '',
    district      VARCHAR(100) DEFAULT '',
    org           VARCHAR(200) DEFAULT '',
    asn           VARCHAR(50)  DEFAULT '',
    is_mobile     BOOLEAN      DEFAULT FALSE,
    is_proxy      BOOLEAN      DEFAULT FALSE,
    is_hosting    BOOLEAN      DEFAULT FALSE,
    browser       VARCHAR(50)  DEFAULT '',
    os            VARCHAR(50)  DEFAULT '',
    device_type   VARCHAR(20)  DEFAULT '',
    created_at    TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visitor_ip ON visitor(ip);
CREATE INDEX IF NOT EXISTS idx_visitor_created ON visitor(created_at DESC);

COMMENT ON TABLE visitor IS '访客记录';
COMMENT ON COLUMN visitor.id IS '主键';
COMMENT ON COLUMN visitor.ip IS '访客 IP';
COMMENT ON COLUMN visitor.path IS '访问路径';
COMMENT ON COLUMN visitor.user_agent IS 'User-Agent';
COMMENT ON COLUMN visitor.city IS '城市';
COMMENT ON COLUMN visitor.region IS '省份/地区';
COMMENT ON COLUMN visitor.country IS '国家';
COMMENT ON COLUMN visitor.district IS '区县';
COMMENT ON COLUMN visitor.org IS '网络运营商';
COMMENT ON COLUMN visitor.asn IS 'ASN';
COMMENT ON COLUMN visitor.is_mobile IS '是否移动网络';
COMMENT ON COLUMN visitor.is_proxy IS '是否代理';
COMMENT ON COLUMN visitor.is_hosting IS '是否机房/托管 IP';
COMMENT ON COLUMN visitor.browser IS '浏览器';
COMMENT ON COLUMN visitor.os IS '操作系统';
COMMENT ON COLUMN visitor.device_type IS '设备类型';
COMMENT ON COLUMN visitor.created_at IS '访问时间';

-- ============================================
-- 默认管理员（密码: admin123）
-- ============================================
INSERT INTO "user" (username, hashed_password, nickname, is_admin)
VALUES (
    'admin',
    '$2b$12$LJ3m4ys4Pz0C5eK8rZqYaOzLiGh5v1DmdMFRnDvMQfLpUfKlPu5S.',
    '管理员',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- ============================================
-- 默认站点配置
-- ============================================
INSERT INTO site_config (key, value, description) VALUES
    ('site_title',       '"Kirameku"',            '站点标题'),
    ('site_description', '"煌めく — 一个个人博客"', '站点描述'),
    ('icp_number',       '""',                    'ICP备案号'),
    ('icp_link',         '""',                    'ICP备案链接')
ON CONFLICT (key) DO NOTHING;
