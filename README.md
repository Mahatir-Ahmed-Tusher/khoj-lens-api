# Khoj Lens API 🔍

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

**Khoj Lens API** is a high-performance, asynchronous REST API wrapper around the `PicImageSearch` Python library. It provides a unified backend endpoint for multi-engine reverse image searching—enabling fact-checkers, bots, web applications, and Android apps to search images concurrently across **13+ reverse image search engines** using a single HTTP request.

---

## 🌟 Key Features

- ⚡ **Asynchronous Concurrency**: Query multiple reverse image search engines in parallel using Python's `asyncio.gather`.
- 🖼️ **Flexible Input**: Accepts image URLs as well as direct file uploads (`multipart/form-data`).
- ⏱️ **Custom Timeout & Error Handling**: Set global request timeouts with graceful fallback for partial engine results.
- 🔐 **Environment-Driven Configuration**: Automatically loads API keys, cookies, and proxy settings from environment variables.
- 🐳 **Docker & Cloud Ready**: Fully containerized and optimized for one-click deployment on platforms like Render, Koyeb, Railway, or Fly.io.

---

## 🛠️ Supported Search Engines (13 Total)

### 1. General Image & Fact-Checking Search Engines (7)
Best for real-world photos, news images, objects, faces, and fact-checking:
- 🔵 **`yandex`** *(Default Choice)*: World-class face recognition and European/Russian web visual data lookup.
- 🔴 **`google_lens`**: Most powerful global visual search and product/object detection.
- 🔷 **`bing`**: Microsoft visual search engine with excellent web image index.
- 👁️ **`tineye`**: Famous for finding exact original image sources and modified image versions.
- 🇨🇳 **`baidu`**: Top Chinese search engine for Asian web visual data.
- 🔍 **`lenso`**: Modern visual search engine for web discovery.
- 🌐 **`copyseeker`**: Image duplication and web page inclusion tracker.

### 2. Anime, Manga & Artwork Search Engines (6)
Tailored specifically for digital art, anime video frames, manga covers, and fanart:
- 🎨 **`saucenao`**: The industry standard for finding anime artwork sources and Pixiv/Twitter illustrators.
- 🎬 **`tracemoe`**: Identifies exact anime titles, episode numbers, and timestamps from video screenshots.
- 🖌️ **`ascii2d`**: Specialist in finding Twitter fanart and Japanese illustration posts.
- 📊 **`iqdb`**: Multi-booru anime image board index search.
- 👤 **`animetrace`**: Anime character facial recognition and series tagging.
- 📖 **`ehentai`**: Manga and doujinshi cover art visual identification.

> 💡 **Performance Tip**: Instead of requesting `"all"` engines, send specific comma-separated engines (e.g., `"google_lens,yandex,bing"`). This reduces server CPU load, prevents `504 Timeout` errors, and delivers ultra-fast results to mobile users!

---

## 📱 Kotlin Android App Integration Guide & Architecture Plan

This section details how to integrate **Khoj Lens API** into a modern Android App using **Kotlin**, **Retrofit**, **Coroutines/Flow**, **Jetpack DataStore**, and **Jetpack Compose**.

```text
Android App Architecture
├── data/
│   ├── api/
│   │   ├── KhojLensApiService.kt    # Retrofit interface (@Multipart @POST("search"))
│   │   └── RetrofitClient.kt         # OkHttp client with timeouts & base URL
│   ├── preferences/
│   │   └── UserPreferences.kt       # DataStore for saving selected search engine
│   └── repository/
│       └── ReverseSearchRepository.kt# Executes API requests & handles errors
├── ui/
│   ├── settings/
│   │   └── SettingsScreen.kt         # Engine selection UI (Default: Yandex)
│   └── search/
│       ├── SearchViewModel.kt        # Manages loading, image Uri, & search results
│       └── ReverseSearchScreen.kt    # Image picker & search result list
└── utils/
    └── FileUtils.kt                  # Converts Android Uri -> MultipartBody.Part
```

---

### Step 1: Add Dependencies (`build.gradle.kts`)

```kotlin
dependencies {
    // Retrofit & OkHttp
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Preferences DataStore
    implementation("androidx.datastore:datastore-preferences:1.0.0")

    // Image Loading (Coil)
    implementation("io.coil-kt:coil-compose:2.6.0")
}
```

---

### Step 2: Engine Preference Manager (`UserPreferences.kt`)

Save the user's preferred search engine in **DataStore**. The default value is set to **`yandex`**.

```kotlin
import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore("user_preferences")

class UserPreferencesManager(private val context: Context) {
    companion object {
        val SELECTED_ENGINE_KEY = stringPreferencesKey("selected_engine")
        const val DEFAULT_ENGINE = "yandex" // Default search engine
    }

    val selectedEngineFlow: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[SELECTED_ENGINE_KEY] ?: DEFAULT_ENGINE
    }

    async fun saveSelectedEngine(engine: String) {
        context.dataStore.edit { prefs ->
            prefs[SELECTED_ENGINE_KEY] = engine
        }
    }
}
```

---

### Step 3: Retrofit API Interface (`KhojLensApiService.kt`)

```kotlin
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface KhojLensApiService {

    @Multipart
    @POST("search")
    suspend fun searchImage(
        @Part("engines") engines: RequestBody,
        @Part file: MultipartBody.Part?,
        @Part("image_url") imageUrl: RequestBody?,
        @Part("timeout_seconds") timeoutSeconds: RequestBody?
    ): Response<Map<String, Any>>
}
```

---

### Step 4: Convert Android Image `Uri` to `MultipartBody.Part` (`FileUtils.kt`)

```kotlin
import android.content.Context
import android.net.Uri
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.InputStream

object FileUtils {
    fun uriToMultipart(context: Context, uri: Uri, partName: String = "file"): MultipartBody.Part? {
        val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
        val bytes = inputStream?.readBytes() ?: return null
        val mimeType = context.contentResolver.getType(uri) ?: "image/jpeg"
        
        val requestBody = bytes.toRequestBody(mimeType.toMediaTypeOrNull())
        return MultipartBody.Part.createFormData(partName, "search_image.jpg", requestBody)
    }

    fun String.toTextRequestBody(): RequestBody {
        return this.toRequestBody("text/plain".toMediaTypeOrNull())
    }
}
```

---

### Step 5: Repository Implementation (`ReverseSearchRepository.kt`)

```kotlin
import android.content.Context
import android.net.Uri
import com.example.khoj.utils.FileUtils.toTextRequestBody
import okhttp3.MultipartBody

sealed class NetworkResult<out T> {
    data class Success<out T>(val data: T) : NetworkResult<T>()
    data class Error(val message: String) : NetworkResult<Nothing>()
    object Loading : NetworkResult<Nothing>()
}

class ReverseSearchRepository(private val apiService: KhojLensApiService) {

    suspend fun searchImage(
        context: Context,
        imageUri: Uri?,
        imageUrlStr: String?,
        selectedEngine: String
    ): NetworkResult<Map<String, Any>> {
        return try {
            val engineBody = selectedEngine.toTextRequestBody()
            val timeoutBody = "30".toTextRequestBody()
            
            val filePart: MultipartBody.Part? = imageUri?.let { 
                FileUtils.uriToMultipart(context, it) 
            }
            val urlBody = imageUrlStr?.takeIf { it.isNotBlank() }?.toTextRequestBody()

            val response = apiService.searchImage(
                engines = engineBody,
                file = filePart,
                imageUrl = urlBody,
                timeoutSeconds = timeoutBody
            )

            if (response.isSuccessful && response.body() != null) {
                NetworkResult.Success(response.body()!!)
            } else {
                NetworkResult.Error("API Search failed: ${response.message()}")
            }
        } catch (e: Exception) {
            NetworkResult.Error("Network error: ${e.localizedMessage ?: "Unknown error"}")
        }
    }
}
```

---

### Step 6: Settings Screen UI (Jetpack Compose)

Allows the user to switch between individual engines or select a combo (e.g. `google_lens,yandex,bing`).

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

val GENERAL_ENGINES = listOf(
    "yandex" to "Yandex (Default - Best for Faces)",
    "google_lens" to "Google Lens (Best for Objects & Global)",
    "bing" to "Bing (Microsoft Visual Search)",
    "google_lens,yandex,bing" to "Fast Combo (Google + Yandex + Bing)",
    "tineye" to "TinEye (Exact Copy & Copyright)",
    "baidu" to "Baidu (Asian Web Data)",
    "all" to "All Engines (May take longer)"
)

@Composable
Composable EngineSettingsScreen(
    currentEngine: String,
    onEngineSelected: (String) -> Unit
) {
    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Select Reverse Search Engine", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(16.dp))

        GENERAL_ENGINES.forEach { (engineKey, displayName) ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
            ) {
                RadioButton(
                    selected = (currentEngine == engineKey),
                    onClick = { onEngineSelected(engineKey) }
                )
                Text(text = displayName, modifier = Modifier.padding(start = 8.dp))
            }
        }
    }
}
```

---

## 🛰️ API Reference

### 1. `GET /`
- **Description**: Root welcome endpoint with API service metadata.
- **Response**:
  ```json
  {
    "status": "ok",
    "message": "Welcome to Khoj Lens API!",
    "docs": "/docs",
    "health": "/health"
  }
  ```

### 2. `GET /health`
- **Description**: Health check endpoint for uptime monitors and load balancers.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

### 3. `POST /search`
- **Description**: Performs reverse image search across one or multiple search engines.
- **Content-Type**: `multipart/form-data`

#### Form Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `engines` | `string` | No | `"all"` | Comma-separated engine names (e.g. `google_lens,yandex,bing`) or `"all"` |
| `image_url` | `string` | Conditional | `null` | Public URL of the image to search |
| `file` | `file` | Conditional | `null` | Multipart file upload |
| `timeout_seconds` | `integer` | No | `30` | Maximum total wait time in seconds for engine tasks |

> ⚠️ **Note**: Either `image_url` or `file` must be provided.

#### Example Request (`cURL` with URL)
```bash
curl -X POST "https://khoj-lens-api.onrender.com/search" \
  -F "engines=google_lens,yandex,bing" \
  -F "image_url=https://example.com/sample.jpg" \
  -F "timeout_seconds=25"
```

#### Example Request (`cURL` with File Upload)
```bash
curl -X POST "https://khoj-lens-api.onrender.com/search" \
  -F "engines=yandex" \
  -F "file=@/path/to/image.jpg"
```

---

## ⚙️ Environment Variables

| Variable | Description |
| :--- | :--- |
| `PROXIES` | Global proxy URL passed to engine network clients (e.g. `http://127.0.0.1:1080`) |
| `GOOGLE_COOKIES` | Raw cookie string used for Google Lens authentication in restricted regions |
| `<ENGINE>_API_KEY` | Engine-specific API key (e.g. `SAUCENAO_API_KEY`, `BAIDU_API_KEY`) |

---

## 🐳 Docker Setup

```bash
# Build Docker image
docker build -t khoj-lens-api .

# Run Docker container
docker run -d -p 8000:8000 --name khoj-lens-service khoj-lens-api
```

---

## ☁️ Cloud Deployment Guides

### Deploying to Render
1. Push your repository to **GitHub**.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your GitHub repository `khoj-lens-api`.
4. Select **Docker** as the Runtime Environment.
5. Select the **Free** instance plan.
6. Click **Create Web Service**.

---

## 📄 License

MIT License © 2026 Khoj Lens Project
