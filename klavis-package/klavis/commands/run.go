package commands

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/spf13/cobra"
)

var runCmd = &cobra.Command{
	Use:   "run [tool]",
	Short: "Run a tool from the Klavis registry",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		tool := args[0]
		image := fmt.Sprintf("ghcr.io/klavis-ai/%s-mcp-server:latest", tool)

		fmt.Println("Running Server:", tool)

		// Build Docker command arguments
		dockerArgs := []string{"run", "--rm", "-it", "-p", "5000:5000"}

		// Only pass KLAVIS_API_KEY if set
		if apiKey := os.Getenv("KLAVIS_API_KEY"); apiKey != "" {
			dockerArgs = append(dockerArgs, "-e", fmt.Sprintf("KLAVIS_API_KEY=%s", apiKey))
		}

		// Append the image name
		dockerArgs = append(dockerArgs, image)

		// Execute Docker
		run := exec.Command("docker", dockerArgs...)
		run.Stdout = os.Stdout
		run.Stderr = os.Stderr
		run.Stdin = os.Stdin

		if err := run.Run(); err != nil {
			fmt.Println("Error running container:", err)
			return
		}
	},
}

func GetRunCommand() *cobra.Command {
	return runCmd
}
