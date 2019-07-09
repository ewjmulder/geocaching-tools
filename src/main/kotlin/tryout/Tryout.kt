package tryout

import java.io.File
import java.util.concurrent.TimeUnit
import kotlinx.serialization.*
import kotlinx.serialization.json.*

import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.transactions.transaction

@Serializable
data class CacheResults(val results: List<CacheResult>, val total: Int)
@Serializable
data class CacheResult(val id: Int)

object Users : Table("users") {
    val id = integer("id").primaryKey()
    val username = varchar("username", 255)
}

//TODO: Correctly type the rest of the columns
//https://github.com/sdeleuze/geospatial-messenger/blob/142f3e5af2ecdd00f6409b9cdf4d63e0d0faaf38/src/main/kotlin/io/spring/messenger/Database.kt#L23
//fun Table.point(name: String, srid: Int = 4326): Column<Point>
//        = registerColumn(name, PointColumnType())

object Caches : Table("caches") {
    val id = integer("id").primaryKey()
    val code = varchar("code", 7)
    val name = varchar("name", 1024)
    val type = varchar("type", 32)
    val location = 
    val status
    val size
    val difficulty
    val terrain
    val placed
    val owner
}

@kotlinx.serialization.UnstableDefault
fun main(args: Array<String>) {
    println("Start gathering caches...")
    val json = "./get_caches.sh 52 5 51 6 0 5".runCommand()
    val results = parse(json)
    println("results: " + results)
    insertInDatabase(results)
}

@kotlinx.serialization.UnstableDefault
fun parse(jsonAsString: String) : CacheResults {
    return Json.nonstrict.parse(CacheResults.serializer(), jsonAsString)
}

fun insertInDatabase(results: CacheResults) {
    Database.connect("jdbc:postgresql://localhost/postgres", driver = "org.postgresql.Driver", user = "postgres", password = "psql")
    transaction {
        addLogger(StdOutSqlLogger)

        SchemaUtils.create(Caches, Users)

        Users.insert {
            it[id] = 1
            it[username] = "user name"
        }

//        Caches.insert {
//        }
    }
}

fun String.runCommand(workingDir: File = File("."),
                      timeoutAmount: Long = 60,
                      timeoutUnit: TimeUnit = TimeUnit.SECONDS): String =
    ProcessBuilder(*this.split("\\s".toRegex()).toTypedArray())
        .directory(workingDir)
        .redirectOutput(ProcessBuilder.Redirect.PIPE)
        .redirectError(ProcessBuilder.Redirect.PIPE)
        .start().apply {
          waitFor(timeoutAmount, timeoutUnit)
        }.inputStream.bufferedReader().readText()

