
CREATE TABLE video_materials (
    id INT AUTO_INCREMENT COMMENT '自增ID',
    material_id VARCHAR(50) NOT NULL COMMENT '素材ID',
    video_url VARCHAR(1024) NOT NULL COMMENT '视频URL',
    preview_url VARCHAR(1024) COMMENT '视频预览URL',
    title VARCHAR(255) COMMENT '视频标题',
    source_type INT NOT NULL DEFAULT 1 COMMENT '视频来源类型 0（站内）,1（站外）',
    campaign_urls TEXT COMMENT '投放链接URL,逗号隔开',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY unique_material_id (material_id)
) ENGINE=InnoDB COMMENT='视频素材表，存储视频素材的基本信息';

CREATE TABLE material_comparison_groups (
    id INT AUTO_INCREMENT COMMENT '自增ID',
    comparison_group_id VARCHAR(50) NOT NULL COMMENT '对比组ID',
    material_id VARCHAR(50) NOT NULL COMMENT '素材ID，关联视频素材表',
    campaign_url VARCHAR(1024) COMMENT '投放链接URL',
    campaign_label VARCHAR(255) COMMENT '投放标签',
    click_count INT DEFAULT 0 COMMENT '点击量',
    completion_count INT DEFAULT 0 COMMENT '完播量',
    like_count INT DEFAULT 0 COMMENT '点赞量',
    comment_count INT DEFAULT 0 COMMENT '评论量',
    share_count INT DEFAULT 0 COMMENT '转发量',
    is_system_preferred BOOLEAN DEFAULT FALSE COMMENT '是否为系统优选',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id)
) ENGINE=InnoDB COMMENT='素材对比组表，用于存储素材的投放效果数据';

