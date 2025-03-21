# Regarding Go content:

### **_REMINDERS_**:
1. **Be sure to periodically run:** 
```bash
gofmt -w <GO FILE PATH>
```
2. **Public func names are in `PascalCase`, while private func names are in `camelCase`**
3. **Get (filter) funcs usually should return a tuple of [Data, errors (if any)] like:**
```go
if val, ok := GetNested(cfg, "geometry", "meta", "created_by"); ok {
	fmt.Println("Found:", val)
```