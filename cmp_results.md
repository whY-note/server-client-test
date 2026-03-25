# 比较结果

## size 比较
一张图片下的 size 比较

| 类型  |size|
|---|---|
|hdf5文件中取出来| 71506 bytes |
|原始帧| 921600 bytes |
|json| 4941319 bytes |  
|msgpack| 921671 bytes |
|pickle | 921671 bytes |

## 以下数据均只传1张图片

### 有VPN

传100条数据，取平均

|   |TCP|Web|
|---|---|---|
|json| 4.8407 s | 5.0969 s |
|msgpack| 0.0125 s | 0.0878 s |
|pickle | 0.0160 s | 0.0960 s |

### 无VPN

传100条数据，取平均

|   |TCP|Web|
|---|---|---|
|json| 4.4829 s |  5.4842 s | 
|msgpack| 0.0136 s | 0.0918 s | 
|pickle | 0.0120 s | 0.0869 s |

## 以下数据仿照实际情况传输

### 有VPN
与服务器测试，局域网

|   |TCP|Web|UDP|
|---|---|---|---|
|jpeg ->原始帧 ->list ->json| 
|jpeg ->json | 0.0250 s | 0.0322 s | |
|jpeg ->原始帧 ->msgpack| 0.1072 s | 0.1118 s | |
|jpeg ->msgpack| 0.0121 s | 0.0288 s | 0.0135 s |
|jpeg ->原始帧 ->pickle | 0.1143 s | 0.1314 s |  |
|jpeg ->pickle|  0.0139 s | 0.0307 s  | |

UDP在测试时经常出现丢包，导致在循环等待，目前只测到了一组

与云服务器测试，公网+隧道
|   |TCP|Web|
|---|---|---|
|jpeg ->原始帧 ->list ->json| 
|jpeg ->json     | 0.0872 s 无 | 0.0881 s 无|
|jpeg ->原始帧 ->msgpack| 0.2777 s | 0.1924 s|
|jpeg ->msgpack| 0.0793 s 无| 0.0855 s 无| 
|jpeg ->原始帧 ->pickle | 0.2720 s | 0.1942 s |
|jpeg ->pickle  | 0.0772 s 无 |0.0807 s 无| 

UDP在测试时经常出现丢包，导致在循环等待

### 无VPN
与服务器测试，局域网

|   |TCP|Web|
|---|---|---|
|jpeg ->原始帧 ->list ->json| (太大，没必要测)|
|jpeg ->json | 0.0249 s | 0.0383 s | 
|jpeg ->原始帧 ->msgpack|  0.0812 s | 0.1051 s |
|jpeg ->msgpack| 0.0138 s| 0.0189 s |
|jpeg ->原始帧 ->pickle | 0.0884 s | 0.1090 s | 
|jpeg ->pickle|  0.0146 s | 0.0195 s |

UDP在测试时经常出现丢包，导致在循环等待

与云服务器测试，公网+隧道
|   |TCP|Web|
|---|---|---|
|jpeg ->原始帧 ->list ->json| 
|jpeg ->json | 0.0933 s 无 | 0.0882 s 无| 
|jpeg ->原始帧 ->msgpack|  0.2931 s | 0.1984 s |
|jpeg ->msgpack| 0.0734 s 无 | 0.0820 s 无| 
|jpeg ->原始帧 ->pickle | 0.3013 s | 0.1976 s |
|jpeg ->pickle| 0.0768 s 无 | 0.0840 s  无| 

UDP在测试时经常出现丢包，导致在循环等待

### 消息总size 比较

| 类型 | total size( 3 pictures + 14 float64)|
|---|---|
|jpeg ->json | 236408 bytes |
|jpeg ->原始帧 ->msgpack| 2765271 bytes |
| jpeg ->msgpack | 183506 bytes |
|jpeg ->原始帧 ->pickle | 2765444 bytes |
| jpeg ->pickle | 183671 bytes|