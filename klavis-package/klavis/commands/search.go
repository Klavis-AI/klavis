package commands

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/spf13/cobra"
)

const RegistryURL = "https://raw.githubusercontent.com/Mayank-MSJ-Singh/Klavis-registry/main/tools.json"

var searchCmd = &cobra.Command{
	Use:   "search",
	Short: "Shows all Servers on Klavis",
	Run: func(cmd *cobra.Command, args []string) {
		resp, err := http.Get(RegistryURL)
		if err != nil {
			cmd.PrintErrln("Error fetching registry:", err)
			return
		}
		defer resp.Body.Close()

		data, err := io.ReadAll(resp.Body)
		if err != nil {
			cmd.PrintErrln("Error reading response:", err)
			return
		}

		var tools map[string]string
		err = json.Unmarshal(data, &tools)
		if err != nil {
			cmd.PrintErrln("Error parsing JSON:", err)
			return
		}

		// Print results
		fmt.Println("Available servers in Klavis:")
		for name := range tools {
			fmt.Printf("- %s\n", name)
		}
	},
}

func GetSearchCommand() *cobra.Command {
	return searchCmd
}
