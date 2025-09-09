package commands

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/spf13/cobra"
)

var uninstallCmd = &cobra.Command{
	Use:   "uninstall [tool]",
	Short: "Uninstall a tool from the Klavis registry",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		tool := args[0]

		image := fmt.Sprintf("ghcr.io/klavis-ai/%s-mcp-server:latest", tool)
		fmt.Println("Uninstalling Server:", tool)

		// Uninstall Docker with interactive terminal
		run := exec.Command("docker", "rmi", image)
		run.Stdout = os.Stdout
		run.Stderr = os.Stderr
		run.Stdin = os.Stdin

		if err := run.Run(); err != nil {
			fmt.Println("Error running container:", err)
			return
		}
	},
}

func GetUninstallCommand() *cobra.Command {
	return uninstallCmd
}
