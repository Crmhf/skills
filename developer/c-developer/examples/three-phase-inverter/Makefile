# 三相并网逆变器 Makefile

# 编译器配置
CC = gcc
CFLAGS = -Wall -Wextra -Werror -O2 -std=c11 \
         -I./inc \
         -D_GNU_SOURCE \
         -ffunction-sections \
         -fdata-sections

# 目标平台配置 (ARM交叉编译时取消注释)
# CROSS_COMPILE = arm-none-eabi-
# CC = $(CROSS_COMPILE)gcc
# CFLAGS += -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

LDFLAGS = -lm

# 源文件
SRC_DIR = src
INC_DIR = inc
OBJ_DIR = obj
BIN_DIR = bin

SOURCES = $(wildcard $(SRC_DIR)/*.c)
OBJECTS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SOURCES))

# 目标
TARGET = $(BIN_DIR)/inverter_sim

# 规则
.PHONY: all clean test directories

all: directories $(TARGET)

directories:
	@mkdir -p $(OBJ_DIR) $(BIN_DIR)

$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "编译完成: $@"

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# 测试目标
test: $(TARGET)
	@echo "运行单元测试..."
	./$(TARGET)

# 静态分析
check:
	cppcheck --enable=all --std=c11 -I$(INC_DIR) $(SRC_DIR)

# 代码格式化
format:
	find $(SRC_DIR) $(INC_DIR) -name "*.c" -o -name "*.h" | xargs clang-format -i

clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)

# 依赖生成
depend: $(SOURCES)
	$(CC) $(CFLAGS) -MM $(SOURCES) > .depend

-include .depend
