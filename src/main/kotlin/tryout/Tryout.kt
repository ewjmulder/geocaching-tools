package tryout

import java.io.File
import java.util.concurrent.TimeUnit
import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class CacheResults(val results: List<CacheResult>, val total: Int)
@Serializable
data class CacheResult(val id: Int)


@kotlinx.serialization.UnstableDefault
fun main(args: Array<String>) {
    println("Start gathering caches...")
    val json = "./get_caches.sh 52 5 51 6 0 5".runCommand()
    val results = parse(json)
    println("results: " + results)
}

@kotlinx.serialization.UnstableDefault
fun parse(jsonAsString: String) : CacheResults {
    return Json.nonstrict.parse(CacheResults.serializer(), jsonAsString)
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

