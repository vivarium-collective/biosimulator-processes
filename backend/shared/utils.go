package shared

func GetNested(spec StateDocument, keys ...string) (interface{}, bool) {
	current := interface{}(spec)
	for _, k := range keys {
		m, ok := current.(map[string]interface{})
		if !ok {
			return nil, false
		}
		current = m[k]
	}
	return current, true
}