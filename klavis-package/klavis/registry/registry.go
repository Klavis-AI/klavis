package registry

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

const RegistryURL = "https://raw.githubusercontent.com/Mayank-MSJ-Singh/Klavis-registry/main/tools.json"

func GetImage(tool string) (string, error) {
	resp, err := http.Get(RegistryURL)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	var tools map[string]string
	err = json.Unmarshal(data, &tools)
	if err != nil {
		return "", err
	}

	image, ok := tools[tool]
	if !ok {
		return "", fmt.Errorf("tool %s not found", tool)
	}

	return image, nil
}
