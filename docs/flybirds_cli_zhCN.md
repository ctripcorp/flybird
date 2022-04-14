# Flybirds  CLI



## **Flybirds  CLI**

**Flybirds  CLI** 是一个命令行应用程序，可以在终端运行使用**Flybirds**创建的简单程序 🚀.

您可以在终端中使用 **Flybirds  CLI** 来运行脚本, 如下:

```bash
flybirds run
```



## 使用

### 安装

要使用 **Flybirds  CLI**，您需要先安装 **flybirds**.

```bash
pip install flybirds
---> 100%
Successfully installed flybirds
```

这就会创建一个你可以在终端调用的 `flybirds` 命令，就像 `python`, `git`, 或`echo`.

```bash
flybirds --help
Usage: flybirds [OPTIONS] COMMAND [ARGS]...

  Welcome to flybirds. Type "--help" for more information.

```



### **命令**

------

你可以指定使用一个下面的 **CLI 命令**:

- `create`:  生成项目 example.

- `run`: 运行项目.




#### 操作

可以在终端输入以下内容来查看**flybirds**运行项目时支持的操作
```bash
flybirds run --help
```


- **--path, -P    TEXT(可选)**

​	指定需要执行的feature集合，可以是目录，也可以指定到具体feature文件，默认是 ‘**features**’ 目录.

示例:

```bash
flybirds run --path ./features/test/demo.feature
```
- **--tag, -T    TEXT(可选)**

​	运行有特定tag的场景，多个用逗号隔开，‘-’开头表示不运行包含此tag的场景
```bash
flybirds run -T tag1,tag2,-tag3,tag4
```
- **--format, -F    TEXT(可选)**

  指定生成测试结果的格式，默认是 json. 

示例:

```bash
#默认
flybirds run --format=json
```

-   **--report, -R   TEXT(可选)**

​	指定生成报告的地址，不指定时默认为 report目录下随机生成的一个文件.

示例：

```bash
#mac 自定义生成报告地址
flybirds run --report report/curent/report.json

#windows 自定义生成报告地址
flybirds run --report report\curent\report.json
```

- **--define, -D   TEXT(可选)**

​	传入用户自定义的参数，此参数有两个作用:

作用1：覆盖`config`配置文件中的相应配置的值，比如：

```bash 
 # 运行时使用的设备和uniqueTag为命令中指定的值，不会取配置文件中配置的值
flybirds run --define deviceId=*** --define uniqueTag=***
```

作用2: 传入自定义参数以便在`pscript`目录下的自定义脚本中使用，使用全局参数 `global_resource` 获取.

- **--rerun  /--no-rerun (可选)**

​	指定失败的场景是否需要重新运行，默认是 ‘True’ ,失败后会自动重跑。

示例：

```bash
#失败场景不重跑
flybirds run --no-rerun 
```

- **--html/--no-html  (可选)**

​	指定case 执行完成后是否生成html测试报告，默认是 ‘True’ ,执行完成后自动生成结果测试报告。

示例：

```bash
#不生成测试报告
flybirds run --no-html
```

- **--processes, -p    INTEGER(可选)**

  指定并发执行时开启进程的最大数量。默认是4 。

  **注意：** 此命令只在 **web** 平台执行时有效。

示例：

```bash
flybirds run --path features -p 5
```

