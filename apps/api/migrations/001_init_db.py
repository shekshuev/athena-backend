from yoyo import step

steps = [
    # ==========================================================
    #  Extensions
    # ==========================================================
    step("create extension if not exists pgcrypto"),
    # ==========================================================
    #  Accounts & Profiles
    # ==========================================================
    step(
        """
        create table accounts (
            id uuid primary key default gen_random_uuid(),
            email text not null,
            password_hash text,
            is_superadmin boolean not null default false,
            status text not null default 'created',
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp,
            confirmed_at timestamp,
            deleted_at timestamp
        )
        """,
        "drop table accounts",
    ),
    step(
        """
        create unique index accounts_email_idx 
        on accounts (email) 
        where deleted_at is null
        """,
        "drop index accounts_email_idx",
    ),
    step(
        """
        create table profiles (
            id uuid primary key default gen_random_uuid(),
            account_id uuid not null references accounts(id) on delete cascade,
            key text not null,
            value text,
            source text,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp,
            unique (account_id, key)
        )
        """,
        "drop table profiles",
    ),
    # ==========================================================
    #  Roles & Permissions (ACL)
    # ==========================================================
    step(
        """
        create table roles (
            id uuid primary key default gen_random_uuid(),
            name text unique not null,
            description text,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp
        )
        """,
        "drop table roles",
    ),
    step(
        """
        create table permissions (
            id uuid primary key default gen_random_uuid(),
            code text unique not null,
            description text not null,
            category text,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp
        )
        """,
        "drop table permissions",
    ),
    step(
        """
        create table role_permissions (
            role_id uuid references roles(id) on delete cascade,
            permission_id uuid references permissions(id) on delete cascade,
            primary key (role_id, permission_id)
        )
        """,
        "drop table role_permissions",
    ),
    step(
        """
        create table account_roles (
            account_id uuid references accounts(id) on delete cascade,
            role_id uuid references roles(id) on delete cascade,
            primary key (account_id, role_id)
        )
        """,
        "drop table account_roles",
    ),
    # ==========================================================
    #  Learning Structure
    # ==========================================================
    step(
        """
        create table courses (
            id uuid primary key default gen_random_uuid(),
            title text not null,
            description text,
            owner_id uuid not null references accounts(id) on delete cascade,
            is_published boolean default false,
            published_at timestamp,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp,
            deleted_at timestamp
        )
        """,
        "drop table courses",
    ),
    step(
        """
        create table lessons (
            id uuid primary key default gen_random_uuid(),
            course_id uuid not null references courses(id) on delete cascade,
            title text not null,
            order_index int not null default 0,
            is_published boolean default false,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp,
            deleted_at timestamp
        )
        """,
        "drop table lessons",
    ),
    step(
        """
        create table steps (
            id uuid primary key default gen_random_uuid(),
            lesson_id uuid not null references lessons(id) on delete cascade,
            title text not null,
            order_index int not null default 0,
            is_mandatory boolean default true,
            is_locked boolean default true,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp
        )
        """,
        "drop table steps",
    ),
    step(
        """
        create table blocks (
            id uuid primary key default gen_random_uuid(),
            step_id uuid not null references steps(id) on delete cascade,
            type text not null,                    -- text, video, quiz, practice, code, etc.
            order_index int not null default 0,
            content_md text,                       -- markdown content
            content_txt text,                      -- plain text for search
            metadata jsonb,                        -- parameters (questions, duration, etc.)
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp
        )
        """,
        "drop table blocks",
    ),
    step(
        """
        create table block_transitions (
            id uuid primary key default gen_random_uuid(),
            from_block uuid not null references blocks(id) on delete cascade,
            to_block uuid not null references blocks(id) on delete cascade,
            condition text not null default 'completed',  -- completed | success | fail | score>70 | timeout | custom
            metadata jsonb,                               -- additional condition params
            created_at timestamp not null default current_timestamp,
            unique (from_block, condition)
        )
        """,
        "drop table block_transitions",
    ),
    step(
        """
        create table user_progress (
            account_id uuid not null references accounts(id) on delete cascade,
            step_id uuid not null references steps(id) on delete cascade,
            is_completed boolean default false,
            score int default 0,
            updated_at timestamp not null default current_timestamp,
            primary key (account_id, step_id)
        )
        """,
        "drop table user_progress",
    ),
    # ==========================================================
    #  Enrollments & Schedule
    # ==========================================================
    step(
        """
        create table enrollments (
            id uuid primary key default gen_random_uuid(),
            account_id uuid not null references accounts(id) on delete cascade,
            course_id uuid not null references courses(id) on delete cascade,
            status text not null default 'active',
            enrolled_at timestamp not null default current_timestamp,
            completed_at timestamp,
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp,
            unique (account_id, course_id)
        )
        """,
        "drop table enrollments",
    ),
    step(
        """
        create table schedule (
            id uuid primary key default gen_random_uuid(),
            course_id uuid not null references courses(id) on delete cascade,
            lesson_id uuid references lessons(id) on delete cascade,
            step_id uuid references steps(id) on delete cascade,
            starts_at timestamp not null,
            ends_at timestamp,
            title text,
            description text,
            type text default 'lesson',  
            created_at timestamp not null default current_timestamp,
            updated_at timestamp not null default current_timestamp,
            deleted_at timestamp
        )
        """,
        "drop table schedule",
    ),
    # ==========================================================
    #  Default Permissions (Seed)
    # ==========================================================
    step(
        """
        insert into permissions (code, description, category) values
        -- === Accounts ===
        ('accounts.create', 'Create accounts', 'accounts'),
        ('accounts.read.any', 'View any account', 'accounts'),
        ('accounts.read.own', 'View own account', 'accounts'),
        ('accounts.update.any', 'Edit any account', 'accounts'),
        ('accounts.update.own', 'Edit own account', 'accounts'),
        ('accounts.delete.any', 'Delete any account', 'accounts'),
        ('accounts.delete.own', 'Delete own account', 'accounts'),

        -- === Profiles ===
        ('profiles.read.any', 'View any profile', 'profiles'),
        ('profiles.read.own', 'View own profile', 'profiles'),
        ('profiles.update.any', 'Edit any profile', 'profiles'),
        ('profiles.update.own', 'Edit own profile', 'profiles'),

        -- === Courses ===
        ('courses.create', 'Create courses', 'courses'),
        ('courses.read.any', 'View any course', 'courses'),
        ('courses.read.own', 'View own courses', 'courses'),
        ('courses.update.any', 'Edit any course', 'courses'),
        ('courses.update.own', 'Edit own course', 'courses'),
        ('courses.delete.any', 'Delete any course', 'courses'),
        ('courses.delete.own', 'Delete own course', 'courses'),
        ('courses.publish', 'Publish courses', 'courses'),

        -- === Lessons ===
        ('lessons.create', 'Create lessons', 'lessons'),
        ('lessons.read.any', 'View any lesson', 'lessons'),
        ('lessons.read.own', 'View own lessons', 'lessons'),
        ('lessons.update.any', 'Edit any lesson', 'lessons'),
        ('lessons.update.own', 'Edit own lesson', 'lessons'),
        ('lessons.delete.any', 'Delete any lesson', 'lessons'),
        ('lessons.delete.own', 'Delete own lesson', 'lessons'),

        -- === Steps ===
        ('steps.create', 'Create steps', 'steps'),
        ('steps.read.any', 'View any step', 'steps'),
        ('steps.read.own', 'View own steps', 'steps'),
        ('steps.update.any', 'Edit any step', 'steps'),
        ('steps.update.own', 'Edit own step', 'steps'),
        ('steps.delete.any', 'Delete any step', 'steps'),
        ('steps.delete.own', 'Delete own step', 'steps'),

        -- === Blocks ===
        ('blocks.create', 'Create blocks (text, video, quiz, etc.)', 'blocks'),
        ('blocks.read.any', 'View any block', 'blocks'),
        ('blocks.read.own', 'View own blocks', 'blocks'),
        ('blocks.update.any', 'Edit any block', 'blocks'),
        ('blocks.update.own', 'Edit own block', 'blocks'),
        ('blocks.delete.any', 'Delete any block', 'blocks'),
        ('blocks.delete.own', 'Delete own block', 'blocks'),
        ('blocks.execute', 'Execute interactive or quiz blocks', 'blocks'),

        -- === Transitions ===
        ('block_transitions.create', 'Create block transitions', 'blocks'),
        ('block_transitions.read', 'View block transitions', 'blocks'),
        ('block_transitions.update', 'Edit block transitions', 'blocks'),
        ('block_transitions.delete', 'Delete block transitions', 'blocks'),

        -- === Progress ===
        ('progress.read', 'View user progress', 'progress'),
        ('progress.update', 'Update user progress', 'progress'),

        -- === Enrollments ===
        ('enrollments.create', 'Enroll users in courses', 'enrollments'),
        ('enrollments.read.any', 'View any enrollment', 'enrollments'),
        ('enrollments.read.own', 'View own enrollments', 'enrollments'),
        ('enrollments.update', 'Update enrollment status', 'enrollments'),
        ('enrollments.delete', 'Unenroll users from courses', 'enrollments'),

        -- === Schedule ===
        ('schedule.create', 'Create schedule entries', 'schedule'),
        ('schedule.read', 'View course schedule', 'schedule'),
        ('schedule.update', 'Edit schedule entries', 'schedule'),
        ('schedule.delete', 'Delete schedule entries', 'schedule'),

        -- === Analytics ===
        ('analytics.view', 'View analytics dashboards', 'analytics'),
        ('analytics.export', 'Export reports', 'analytics'),

        -- === System ===
        ('system.settings.view', 'View system settings', 'system'),
        ('system.settings.update', 'Update system settings', 'system')
        """,
        "delete from permissions",
    ),
    # ==========================================================
    #  Default Roles (Seed)
    # ==========================================================
    step(
        """
        insert into roles (name, description) values
        ('admin', 'Full access to all system resources'),
        ('teacher', 'Create and manage own courses and materials'),
        ('student', 'View published content and take tests'),
        ('moderator', 'Moderate content and manage users'),
        ('guest', 'Limited read-only access to public content')
        """,
        "delete from roles",
    ),
]
