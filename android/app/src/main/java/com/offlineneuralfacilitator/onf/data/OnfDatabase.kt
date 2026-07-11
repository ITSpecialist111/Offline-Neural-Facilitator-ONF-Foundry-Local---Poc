package com.offlineneuralfacilitator.onf.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.offlineneuralfacilitator.onf.domain.model.OnfState
import com.offlineneuralfacilitator.onf.rag.KnowledgeChunk

internal class OnfDatabase(context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {
    override fun onCreate(database: SQLiteDatabase) {
        database.execSQL(
            """
            CREATE TABLE session_snapshots (
                id TEXT PRIMARY KEY NOT NULL,
                topic TEXT NOT NULL,
                updated_at INTEGER NOT NULL,
                payload TEXT NOT NULL
            )
            """.trimIndent(),
        )
        database.execSQL("CREATE INDEX session_snapshots_updated ON session_snapshots(updated_at DESC)")
        database.execSQL(
            """
            CREATE TABLE knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seed_key TEXT NOT NULL,
                source TEXT NOT NULL,
                section TEXT NOT NULL,
                body TEXT NOT NULL,
                curated INTEGER NOT NULL DEFAULT 0
            )
            """.trimIndent(),
        )
        database.execSQL("CREATE INDEX knowledge_chunks_seed ON knowledge_chunks(seed_key)")
    }

    override fun onUpgrade(database: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun save(state: OnfState) {
        writableDatabase.insertWithOnConflict(
            "session_snapshots",
            null,
            ContentValues().apply {
                put("id", state.session.id)
                put("topic", state.session.topic)
                put("updated_at", System.currentTimeMillis())
                put("payload", SessionJsonCodec.encode(state))
            },
            SQLiteDatabase.CONFLICT_REPLACE,
        )
    }

    fun latest(): OnfState? = readableDatabase.query(
        "session_snapshots",
        arrayOf("payload"),
        null,
        null,
        null,
        null,
        "updated_at DESC",
        "1",
    ).use { cursor ->
        if (!cursor.moveToFirst()) null else runCatching { SessionJsonCodec.decode(cursor.getString(0)) }.getOrNull()
    }

    fun replaceKnowledge(
        seedKey: String,
        sections: List<MarkdownSection>,
        curated: Boolean,
    ): Int {
        val database = writableDatabase
        var inserted = 0
        database.beginTransaction()
        try {
            database.delete("knowledge_chunks", "seed_key = ?", arrayOf(seedKey))
            sections.forEach { section ->
                MarkdownSections.chunks(section.body).forEach { body ->
                    database.insertOrThrow(
                        "knowledge_chunks",
                        null,
                        ContentValues().apply {
                            put("seed_key", seedKey)
                            put("source", section.source)
                            put("section", section.heading)
                            put("body", body)
                            put("curated", if (curated) 1 else 0)
                        },
                    )
                    inserted += 1
                }
            }
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
        return inserted
    }

    fun knowledge(): List<KnowledgeChunk> = readableDatabase.query(
        "knowledge_chunks",
        arrayOf("id", "source", "section", "body", "curated"),
        null,
        null,
        null,
        null,
        "source, section, id",
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                add(
                    KnowledgeChunk(
                        id = cursor.getLong(0),
                        source = cursor.getString(1),
                        section = cursor.getString(2),
                        text = cursor.getString(3),
                        curated = cursor.getInt(4) == 1,
                    ),
                )
            }
        }
    }

    fun knowledgeCount(): Int = readableDatabase.rawQuery("SELECT COUNT(*) FROM knowledge_chunks", null).use {
        if (it.moveToFirst()) it.getInt(0) else 0
    }

    companion object {
        private const val DATABASE_NAME = "onf_private.db"
        private const val DATABASE_VERSION = 1
    }
}
