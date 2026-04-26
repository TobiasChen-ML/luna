import sqlite3
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import json
import aiosqlite

from app.core.config import resolve_sqlite_path, settings


class Database:
    _instance: Optional["Database"] = None
    _db_path: Path

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_path = Path(resolve_sqlite_path(settings.database_url))
        return cls._instance

    async def connect(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await self._create_tables(db)

    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                avatar_url TEXT,
                tier TEXT DEFAULT 'free',
                credits REAL DEFAULT 0,
                purchased_credits REAL DEFAULT 0,
                monthly_credits REAL DEFAULT 0,
                user_type TEXT DEFAULT 'free',
                subscription_period TEXT,
                subscription_start_date TIMESTAMP,
                subscription_end_date TIMESTAMP,
                stripe_customer_id TEXT,
                last_monthly_credit_grant TIMESTAMP,
                signup_bonus_granted INTEGER DEFAULT 0,
                total_credits_earned REAL DEFAULT 0,
                total_credits_spent REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT NOT NULL,
                provider TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                input TEXT,
                result_url TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                content TEXT NOT NULL,
                layer TEXT DEFAULT 'episodic',
                embedding BLOB,
                metadata TEXT,
                importance INTEGER DEFAULT 5,
                decayed_importance REAL DEFAULT 5.0,
                last_accessed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_memories_user_character ON memories(user_id, character_id);
            CREATE INDEX IF NOT EXISTS idx_memories_layer ON memories(layer);
            CREATE INDEX IF NOT EXISTS idx_memories_decayed ON memories(decayed_importance DESC);

            CREATE TABLE IF NOT EXISTS global_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'preference',
                source_character_id TEXT,
                confidence REAL DEFAULT 1.0,
                reference_count INTEGER DEFAULT 1,
                is_confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_global_memories_user ON global_memories(user_id);
            CREATE INDEX IF NOT EXISTS idx_global_memories_category ON global_memories(category);

            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_subscription_id TEXT,
                status TEXT DEFAULT 'active',
                tier TEXT NOT NULL,
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revoked_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS media_assets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_id TEXT,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                thumbnail_url TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS batch_jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                total INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                first_name TEXT,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                age INTEGER,
                gender TEXT DEFAULT 'female',
                ethnicity TEXT,
                nationality TEXT,
                occupation TEXT,
                top_category TEXT DEFAULT 'girls',
                sub_category TEXT,
                filter_tags TEXT,
                personality_tags TEXT,
                keywords TEXT,
                personality_summary TEXT,
                personality_example TEXT,
                backstory TEXT,
                system_prompt TEXT,
                greeting TEXT,
                avatar_url TEXT,
                cover_url TEXT,
                avatar_card_url TEXT,
                profile_image_url TEXT,
                preview_video_url TEXT,
                mature_image_url TEXT,
                mature_cover_url TEXT,
                mature_video_url TEXT,
                voice_id TEXT,
                meta_title TEXT,
                meta_description TEXT,
                seo_optimized INTEGER DEFAULT 0,
                is_official INTEGER DEFAULT 1,
                is_public INTEGER DEFAULT 1,
                template_id TEXT,
                generation_mode TEXT DEFAULT 'manual',
                popularity_score REAL DEFAULT 0.0,
                chat_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                creator_id TEXT,
                family_id TEXT,
                lifecycle_status TEXT DEFAULT 'active',
                review_status TEXT DEFAULT 'approved',
                reviewed_at TIMESTAMP,
                reviewer_id TEXT,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extra_data TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_characters_slug ON characters(slug);
            CREATE INDEX IF NOT EXISTS idx_characters_top_category ON characters(top_category);
            CREATE INDEX IF NOT EXISTS idx_characters_is_official ON characters(is_official);
            CREATE INDEX IF NOT EXISTS idx_characters_is_public ON characters(is_public);
            CREATE INDEX IF NOT EXISTS idx_characters_popularity ON characters(popularity_score DESC);

            CREATE TABLE IF NOT EXISTS character_script_bindings (
                character_id TEXT NOT NULL,
                script_id TEXT NOT NULL,
                weight INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (character_id, script_id),
                FOREIGN KEY (character_id) REFERENCES characters(id),
                FOREIGN KEY (script_id) REFERENCES script_library(id)
            );
            CREATE INDEX IF NOT EXISTS idx_character_script_bindings_character ON character_script_bindings(character_id);
            CREATE INDEX IF NOT EXISTS idx_character_script_bindings_script ON character_script_bindings(script_id);

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                participants TEXT,
                script_id TEXT,
                script_state TEXT,
                script_node_id TEXT,
                quest_progress REAL DEFAULT 0,
                title TEXT,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_message_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user_character ON chat_sessions(user_id, character_id);

            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                character_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                speaker_id TEXT,
                message_type TEXT DEFAULT 'text',
                audio_url TEXT,
                image_urls TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session_created ON chat_messages(session_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_messages_user_character ON chat_messages(user_id, character_id);

            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                script_id TEXT,
                intimacy REAL DEFAULT 0,
                trust REAL DEFAULT 0,
                desire REAL DEFAULT 0,
                dependency REAL DEFAULT 0,
                stage TEXT DEFAULT 'stranger',
                is_locked INTEGER DEFAULT 0,
                locked_at TIMESTAMP,
                history_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, character_id)
            );
            CREATE INDEX IF NOT EXISTS idx_relationships_user_character ON relationships(user_id, character_id);

            CREATE TABLE IF NOT EXISTS prompt_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                variables TEXT,
                version INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 100,
                description TEXT,
                description_zh TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_templates_category_active ON prompt_templates(category, is_active);

            CREATE TABLE IF NOT EXISTS scripts (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                genre TEXT,
                world_setting TEXT,
                world_rules TEXT,
                character_role TEXT,
                character_setting TEXT,
                user_role TEXT,
                user_role_description TEXT,
                nodes TEXT,
                start_node_id TEXT,
                opening_scene TEXT,
                opening_line TEXT,
                emotion_gates TEXT,
                triggers TEXT,
                tags TEXT,
                difficulty TEXT DEFAULT 'normal',
                estimated_duration INTEGER,
                play_count INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 1,
                is_official INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_scripts_character ON scripts(character_id);

            CREATE TABLE IF NOT EXISTS script_nodes (
                id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                node_type TEXT NOT NULL,
                title TEXT,
                description TEXT,
                narrative TEXT,
                character_inner_state TEXT,
                choices TEXT,
                effects TEXT,
                triggers TEXT,
                media_cue TEXT,
                prerequisites TEXT,
                emotion_gate TEXT,
                position_x INTEGER DEFAULT 0,
                position_y INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_nodes_script ON script_nodes(script_id);

            CREATE TABLE IF NOT EXISTS script_reviews (
                id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                action TEXT NOT NULL,
                previous_status TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts(id)
            );
            CREATE INDEX IF NOT EXISTS idx_reviews_script ON script_reviews(script_id);
            CREATE INDEX IF NOT EXISTS idx_reviews_action ON script_reviews(action);

            CREATE TABLE IF NOT EXISTS story_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                story_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                status TEXT DEFAULT 'in_progress',
                current_node_id TEXT,
                visited_nodes TEXT,
                choices_made TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                ending_type TEXT,
                completion_time_minutes INTEGER,
                archived INTEGER DEFAULT 0,
                play_index INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (story_id) REFERENCES scripts(id)
            );
            CREATE INDEX IF NOT EXISTS idx_story_progress_user ON story_progress(user_id);
            CREATE INDEX IF NOT EXISTS idx_story_progress_story ON story_progress(story_id);
            CREATE INDEX IF NOT EXISTS idx_story_progress_archived ON story_progress(archived);

            CREATE TABLE IF NOT EXISTS story_nodes (
                id TEXT PRIMARY KEY,
                story_id TEXT NOT NULL,
                sequence INTEGER DEFAULT 0,
                title TEXT,
                narrative_phase TEXT DEFAULT 'opening',
                location TEXT,
                scene_description TEXT,
                character_context TEXT,
                response_instructions TEXT,
                max_turns_in_node INTEGER DEFAULT 3,
                choices TEXT,
                auto_advance TEXT,
                is_ending_node INTEGER DEFAULT 0,
                ending_type TEXT,
                trigger_image INTEGER DEFAULT 0,
                image_prompt_hint TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES scripts(id)
            );
            CREATE INDEX IF NOT EXISTS idx_story_nodes_story ON story_nodes(story_id);

            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE,
                description TEXT,
                cover_image_url TEXT,
                author_type TEXT DEFAULT 'admin',
                author_id TEXT,
                status TEXT DEFAULT 'draft',
                is_official INTEGER DEFAULT 0,
                entry_conditions TEXT,
                start_node_id TEXT,
                total_nodes INTEGER DEFAULT 0,
                ai_trigger_keywords TEXT,
                completion_rewards TEXT,
                play_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters(id)
            );
            CREATE INDEX IF NOT EXISTS idx_stories_character ON stories(character_id);
            CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);

            CREATE TABLE IF NOT EXISTS safety_rules (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                patterns TEXT,
                action TEXT DEFAULT 'block',
                redirect_message TEXT,
                is_active INTEGER DEFAULT 1,
                severity INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS credit_cost_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_cost REAL DEFAULT 0.1,
                voice_cost REAL DEFAULT 0.2,
                image_cost INTEGER DEFAULT 2,
                video_cost INTEGER DEFAULT 4,
                voice_call_per_minute INTEGER DEFAULT 3,
                signup_bonus_credits INTEGER DEFAULT 10,
                premium_monthly_credits INTEGER DEFAULT 100,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            );

            CREATE TABLE IF NOT EXISTS credit_packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pack_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                credits INTEGER NOT NULL,
                price_cents INTEGER NOT NULL,
                bonus_credits INTEGER DEFAULT 0,
                is_popular INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT UNIQUE NOT NULL,
                price_cents INTEGER NOT NULL,
                monthly_equivalent_cents INTEGER NOT NULL,
                discount_percent INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT NOT NULL,
                admin_email TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_audit_logs_admin ON audit_logs(admin_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                usage_type TEXT,
                credit_source TEXT,
                order_id TEXT,
                character_id TEXT,
                session_id TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_credit_transactions_user ON credit_transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_credit_transactions_created ON credit_transactions(created_at);

            CREATE TABLE IF NOT EXISTS config_presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                config_json TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                is_builtin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_config_presets_category ON config_presets(category);
            CREATE INDEX IF NOT EXISTS idx_config_presets_active ON config_presets(category, is_active);

            CREATE TABLE IF NOT EXISTS voices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                preview_url TEXT,
                provider TEXT NOT NULL DEFAULT 'elevenlabs',
                provider_voice_id TEXT NOT NULL,
                model_id TEXT,
                language TEXT DEFAULT 'en',
                gender TEXT DEFAULT 'female',
                tone TEXT,
                settings TEXT DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_voices_provider ON voices(provider);
            CREATE INDEX IF NOT EXISTS idx_voices_language ON voices(language);
            CREATE INDEX IF NOT EXISTS idx_voices_is_active ON voices(is_active);

            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                is_secret INTEGER DEFAULT 0,
                updated_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS openpose_presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                image_url TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_openpose_presets_active ON openpose_presets(is_active);
        """)
        await self._ensure_prompt_templates_schema(db)
        await db.commit()

    async def _ensure_prompt_templates_schema(self, db: aiosqlite.Connection) -> None:
        cursor = await db.execute("PRAGMA table_info(prompt_templates)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "description_zh" not in columns:
            await db.execute("ALTER TABLE prompt_templates ADD COLUMN description_zh TEXT")

    async def execute(
        self,
        query: str,
        params: tuple = (),
        fetch: bool = False,
        fetch_all: bool = False,
    ) -> Any:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            if fetch_all:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            if fetch:
                row = await cursor.fetchone()
                return dict(row) if row else None
            await db.commit()
            return cursor.lastrowid


db = Database()
