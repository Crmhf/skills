# RTOS 实时操作系统设计模式

嵌入式实时操作系统开发的模式与最佳实践。

## 目录

- [任务设计](#任务设计)
- [同步机制](#同步机制)
- [内存管理](#内存管理)
- [中断处理](#中断处理)

---

## 任务设计

### 任务分类

| 任务类型 | 优先级 | 周期 | 用途 |
|----------|--------|------|------|
| **中断服务** | 最高 | 微秒级 | 硬件响应 |
| **实时任务** | 高 | 毫秒级 | 控制算法 |
| **常规任务** | 中 | 十毫秒级 | 数据处理 |
| **后台任务** | 低 | 秒级 | 日志/维护 |

### 任务创建示例

```c
// FreeRTOS 任务创建
void vSensorTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();

    for(;;) {
        // 读取传感器数据
        float temperature = readTemperature();
        float humidity = readHumidity();

        // 数据处理
        processSensorData(temperature, humidity);

        // 精确周期控制 (10ms)
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(10));
    }
}

// 任务创建
xTaskCreate(
    vSensorTask,
    "Sensor",
    configMINIMAL_STACK_SIZE,
    NULL,
    tskIDLE_PRIORITY + 2,
    NULL
);
```

---

## 同步机制

### 信号量使用

```c
// 二值信号量 - 任务同步
SemaphoreHandle_t xDataReadySemaphore;

void vProducerTask(void *pv) {
    for(;;) {
        // 生产数据
        produceData();

        // 通知消费者
        xSemaphoreGive(xDataReadySemaphore);
    }
}

void vConsumerTask(void *pv) {
    for(;;) {
        // 等待数据就绪
        if(xSemaphoreTake(xDataReadySemaphore, portMAX_DELAY) == pdTRUE) {
            // 消费数据
            consumeData();
        }
    }
}
```

### 互斥锁保护

```c
// 保护共享资源
SemaphoreHandle_t xMutex;
int sharedCounter = 0;

void vSafeIncrement(void) {
    if(xSemaphoreTake(xMutex, portMAX_DELAY) == pdTRUE) {
        sharedCounter++;
        xSemaphoreGive(xMutex);
    }
}
```

### 队列通信

```c
// 数据队列
QueueHandle_t xDataQueue;

// 定义数据包
typedef struct {
    uint32_t timestamp;
    float value;
    uint8_t sensorId;
} SensorData_t;

// 创建队列
xDataQueue = xQueueCreate(10, sizeof(SensorData_t));

// 发送
SensorData_t data = {xTaskGetTickCount(), 25.5, 1};
xQueueSend(xDataQueue, &data, portMAX_DELAY);

// 接收
SensorData_t received;
xQueueReceive(xDataQueue, &received, portMAX_DELAY);
```

---

## 内存管理

### 静态内存分配

```c
// 推荐：静态分配避免碎片
static uint8_t ucHeap[configTOTAL_HEAP_SIZE];

// 静态任务栈
static StaticTask_t xTaskBuffer;
static StackType_t xStack[256];

TaskHandle_t xTask = xTaskCreateStatic(
    vTaskFunction,
    "Task",
    256,
    NULL,
    1,
    xStack,
    &xTaskBuffer
);
```

### 内存池

```c
// 固定大小内存池
typedef struct {
    uint8_t buffer[32];
    bool used;
} MemoryBlock_t;

#define POOL_SIZE 10
static MemoryBlock_t memoryPool[POOL_SIZE];

void* poolAlloc(void) {
    for(int i = 0; i < POOL_SIZE; i++) {
        if(!memoryPool[i].used) {
            memoryPool[i].used = true;
            return memoryPool[i].buffer;
        }
    }
    return NULL;
}

void poolFree(void* ptr) {
    for(int i = 0; i < POOL_SIZE; i++) {
        if(memoryPool[i].buffer == ptr) {
            memoryPool[i].used = false;
            return;
        }
    }
}
```

---

## 中断处理

### 中断服务程序设计

```c
// 中断处理原则：快速退出
void EXTI_IRQHandler(void) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    // 清除中断标志
    EXTI_ClearITPendingBit(EXTI_Line0);

    // 通知任务处理 (非阻塞)
    xSemaphoreGiveFromISR(xButtonSemaphore, &xHigherPriorityTaskWoken);

    // 上下文切换
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

### 延迟处理模式

```c
// 中断只做标记，任务做实际处理
void vButtonHandlerTask(void *pv) {
    for(;;) {
        if(xSemaphoreTake(xButtonSemaphore, portMAX_DELAY)) {
            // 消抖
            vTaskDelay(pdMS_TO_TICKS(20));

            // 确认按键状态
            if(GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0)) {
                // 处理按键
                handleButtonPress();
            }
        }
    }
}
```

---

## 检查清单

- [ ] 任务优先级是否合理？
- [ ] 共享资源是否正确保护？
- [ ] 中断处理是否足够简短？
- [ ] 内存使用是否可预测？
- [ ] 是否避免了优先级反转？
