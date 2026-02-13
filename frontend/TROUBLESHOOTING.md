# 🔧 故障排除指南

## 问题：Failed to resolve import "@tanstack/react-query"

### 解决方案

#### 1. 重新安装依赖（已完成）
```bash
cd frontend
npm install
```

#### 2. 如果问题仍然存在，清除缓存重新安装
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### 3. 检查 node_modules 是否存在
```bash
ls node_modules/@tanstack/react-query
```

如果目录不存在，说明安装失败，需要重新安装。

#### 4. 重启开发服务器
```bash
# 停止当前服务器（Ctrl+C）
# 然后重新启动
npm run dev
```

#### 5. 如果使用 VS Code，重启 IDE
有时候 IDE 的 TypeScript 服务器需要重启才能识别新安装的包。

## 其他常见问题

### 端口被占用
```bash
# 修改 vite.config.ts 中的端口号
server: {
  port: 5174,  # 改为其他端口
}
```

### TypeScript 类型错误
```bash
# 重启 TypeScript 服务器
# VS Code: Cmd+Shift+P -> "TypeScript: Restart TS Server"
```

### 依赖版本冲突
```bash
# 查看依赖树
npm ls @tanstack/react-query

# 如果版本不对，删除 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install
```

## 验证安装

运行以下命令验证所有依赖是否正确安装：

```bash
npm list --depth=0
```

应该能看到所有依赖包，包括：
- react
- react-dom
- @tanstack/react-query
- react-router-dom
- axios
- recharts
- react-markdown
- @heroicons/react
