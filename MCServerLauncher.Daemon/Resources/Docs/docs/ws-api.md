### FileUploadRequest

文件上传至后端前的请求，需要提供上传的目标路径，文件校验码和文件大小，由于使用分块传输，故还需提供分块大小。

后端接受请求后:

1. 检查chunk_size和size是否在正int范围、chunk_size是否不大于size。
2. 检查后端是否有同名的文件正在上传。
3. 预分配空间，生成file_id。
4. 回应file_id。

(虽然chunk_size和size都是long处理，但是C#的FileStream.Write方法只支持int范围的寻址，故文件大小不宜超过2GB (2^31-1 B)
，如果超过会返回error)

##### 请求

```json
{
    "action": "file_upload_request",
    "params":{
        "path": "path/to/file",
        "sha1": "114514114514114514114514114514",
        "chunk_size": 1024,
        "size": 1919810
    }
}
```

| 参数         | 值    | 含义           |
|------------|------|--------------|
| path       | str  | 上传的文件将要存放的位置 |
| sha1       | str  | 文件SHA-1校验码   |
| chunk_size | long | 分块传输的分块大小    |
| size       | long | 文件总大小        |

##### 响应

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "file_id": "abcdefg-hijk-lmno-pqrstyvw"
    }
}
```

| 参数      | 值   | 含义        |
|---------|-----|-----------|
| file_id | str | 文件上传句柄/标识 |

### FileUploadChunk

成功申请到file_id后，即可上传文件的分块数据，此时需要提供file_id，分块偏移量，分块数据。

后端接受到此请求后:

1. 检查offset是否大于0且小于文件长度。
2. 将data按大端解码为byte[]。
3. 按偏移量和计算的分块长度写入文件。
4. 检查文件是否下载完毕，若下载完毕，校验SHA-1。

##### 请求

```json
{
    "action": "file_upload_chunk",
    "params":{
        "file_id": "abcdefg-hijk-lmno-pqrstyvw",
        "offset": 114514,
        "data": "????????????????????????????????????????????????????????????????????????????????????????????????????????"
    }
}
```

| 参数      | 值    | 含义            |
|---------|------|---------------|
| file_id | str  | 文件上传句柄/标识     |
| offset  | long | 分块偏移量         |
| data    | str  | 字符串形式的bytes[] |

##### 响应

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "done": false,
        "received": 1048576
    }
}
```

| 参数       | 值    | 含义      |
|----------|------|---------|
| done     | bool | 是否上传完毕  |
| received | long | 已接受的字节数 |

### FileUploadCancel

通过file_id取消上传的任务

后端接受到此请求后:

1. 从uploadSessions取出该上传info
2. 关闭文件指针，并删除临时文件

##### 请求

```json
{
    "action": "file_upload_cancel",
    "params":{
        "file_id": "..."
    }
}
```

| 参数名     | 值   | 含义              |
|---------|-----|-----------------|
| file_id | str | 要取消上传任务的file_id |

##### 响应

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {}
}
```

该响应无参数

### GetJavaList

获取java列表不一定是实时的，他是基于时间缓存的，一次请求后最多**<u>60s</u>**
就会使得下次请求重新扫描java列表（由于人们并不会频繁的为计算机增减jre，故使用IAsyncTimedCacheable去缓存java扫描结果以优化整体性能，尤其是请求高峰期）。

具体代码细节参考Daemon\Program.cs的ConfigureService中IAsyncTimedCacheable<List<JavaScanner.JavaInfo>>单例。

##### 请求

```json
{
    "action": "get_java_list",
    "params":{}
}
```

该请求无参数

##### 响应

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "java_list": [
            {
                "path": "C:\\Program Files\\Common Files\\Oracle\\Java\\javapath\\java.exe",
                "version": "21.0.1",
                "architecture": "x64"
            },
            {
                "path": "C:\\Program Files\\Common Files\\Oracle\\Java\\javapath_target_233021531\\java.exe",
                "version": "21.0.1",
                "architecture": "x64"
            },
            ...
        ]
    }
}
```

| 参数名       | 值          | 含义          |
|-----------|------------|-------------|
| java_list | JavaInfo[] | 包含java信息的列表 |

其中JavaInfo定义如下

```c#
public struct JavaInfo
{
    public string Path { get; set; }
    public string Version { get; set; }
    public string Architecture { get; set; }

    public override string ToString()
    {
        return JsonConvert.SerializeObject(this, Formatting.Indented);
    }
}
```

### HeartBeat

最简单的请求：客户端发送一个包，服务端返回一个应答。

##### 请求

```json
{
    "action": "get_java_list",
    "params":{}
}
```

##### 应答

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "time": 1723550404
  }
}
```

| 参数名 | 值   | 含义                             |
| ------ | ---- | -------------------------------- |
| time   | long | heartbeat请求应答的Unix时间戳(s) |
