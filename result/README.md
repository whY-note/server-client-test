# Result

## 表格字段含义解释

`all_tests.csv` 每一行表示一次测试的汇总结果。

| 字段 | 含义 |
|---|---|
| user_name | 用户名/实验名 |
| packaging_type | 序列化方式（json / msgpack / pickle） |
| test_num | 本次测试步数（通常即交互帧数） |
| avg_decode_time | 平均解码耗时（秒/步） |
| avg_RTT | 平均往返时延 RTT（秒） |
| total_decode_time | 总解码耗时（秒） |
| total_elapsed_time | 本次测试总耗时（秒） |
| total_round_trip_time | RTT 总和（秒） |
| avg_step_time | 平均每步耗时（秒/步） |
| min_RTT | RTT 最小值（秒） |
| p50_RTT | RTT 50 分位（中位数，秒） |
| p95_RTT | RTT 95 分位（秒） |
| max_RTT | RTT 最大值（秒） |
| std_RTT | RTT 标准差（秒） |
| fps | 实际处理帧率（步/秒） |
| timeout_count | 超时次数 |
| successful_action_count | 成功收到并执行 action 的次数 |
| action_success_rate | action 成功率（successful_action_count / test_num） |
| decode_time_ratio | 解码时间占总时间比例（total_decode_time / total_elapsed_time） |
| total_obs_payload_bytes | 观测数据 payload 总字节数（不含额外协议开销） |
| avg_obs_payload_bytes | 每步观测 payload 平均字节数 |
| min_obs_payload_bytes | 每步观测 payload 最小字节数 |
| p50_obs_payload_bytes | 每步观测 payload 中位数 |
| p95_obs_payload_bytes | 每步观测 payload 95 分位 |
| max_obs_payload_bytes | 每步观测 payload 最大值 |
| total_obs_wire_bytes_est | 观测数据线上传输字节估计总量（含协议开销估计） |
| avg_obs_wire_bytes_est | 每步观测线上字节估计均值 |
| min_obs_wire_bytes_est | 每步观测线上字节估计最小值 |
| p50_obs_wire_bytes_est | 每步观测线上字节估计中位数 |
| p95_obs_wire_bytes_est | 每步观测线上字节估计 95 分位 |
| max_obs_wire_bytes_est | 每步观测线上字节估计最大值 |
| total_action_payload_bytes | action payload 总字节数 |
| avg_action_payload_bytes | 每步 action payload 平均字节数 |
| min_action_payload_bytes | 每步 action payload 最小字节数 |
| p50_action_payload_bytes | 每步 action payload 中位数 |
| p95_action_payload_bytes | 每步 action payload 95 分位 |
| max_action_payload_bytes | 每步 action payload 最大值 |
| total_action_wire_bytes_est | action 线上字节估计总量 |
| avg_action_wire_bytes_est | 每步 action 线上字节估计均值 |
| min_action_wire_bytes_est | 每步 action 线上字节估计最小值 |
| p50_action_wire_bytes_est | 每步 action 线上字节估计中位数 |
| p95_action_wire_bytes_est | 每步 action 线上字节估计 95 分位 |
| max_action_wire_bytes_est | 每步 action 线上字节估计最大值 |
| total_payload_bytes | obs + action 的 payload 总字节数 |
| total_wire_bytes_est | obs + action 的线上字节估计总量 |
| avg_total_payload_bytes | 每步总 payload 平均字节数 |
| avg_total_wire_bytes_est | 每步总线上字节估计均值 |
| goodput_mbps | 仅按 payload 计算的吞吐（Mbps） |
| wire_goodput_mbps | 按 wire 字节估计计算的吞吐（Mbps） |
| status | 测试状态（如 success） |
| protocol | 传输协议（tcp / web / udp） |
| config | 使用的配置名（例如 test_1） |
| is_jpeg | 图像是否 JPEG 压缩（True/False） |

### 快速关注指标

- 延迟：`avg_RTT`, `p95_RTT`, `max_RTT`
- 稳定性：`timeout_count`, `action_success_rate`
- 实时性：`fps`, `avg_step_time`
- 带宽/开销：`goodput_mbps`, `wire_goodput_mbps`, `avg_total_wire_bytes_est`


