package commands

import (
	"fmt"
	"os/exec"
	"strings"

	"github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "Shows all downloaded Servers",
	Run: func(cmd *cobra.Command, args []string) {
		// Run `docker images` and get all image names
		run := exec.Command("docker", "images", "--format", "{{.Repository}}:{{.Tag}}")
		out, err := run.Output()
		if err != nil {
			fmt.Println("Error running docker images:", err)
			return
		}

		// Filter for Klavis images
		lines := strings.Split(string(out), "\n")
		klavisList := []string{}
		for _, line := range lines {
			if strings.Contains(line, "klavis-ai") {
				klavisList = append(klavisList, line)
			}
		}

		// Print results
		fmt.Println("Klavis images installed:")
		for _, img := range klavisList {
			// Remove prefix
			name := strings.TrimPrefix(img, "ghcr.io/klavis-ai/")
			// Remove suffix
			name = strings.TrimSuffix(name, "-mcp-server:latest")

			fmt.Println(name)
		}

		// Optional: print count
		fmt.Printf("Total Klavis Servers: %d\n", len(klavisList))
	},
}

func GetListCommand() *cobra.Command {
	return listCmd
}
