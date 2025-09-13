package commands

import (
	"fmt"
	"os/exec"

	"klavis/registry"

	"github.com/spf13/cobra"
)

var installCmd = &cobra.Command{
	Use:   "install [tool]",
	Short: "Install a tool from the Klavis registry",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		tool := args[0]

		image, err := registry.GetImage(tool)
		if err != nil {
			fmt.Println("Error fetching image:", err)
			return
		}

		fmt.Println("Pulling Docker image:", image)

		pull := exec.Command("docker", "pull", image)
		pull.Stdout = cmd.OutOrStdout()
		pull.Stderr = cmd.OutOrStderr()

		if err := pull.Run(); err != nil {
			fmt.Println("Error pulling image:", err)
			return
		}

		fmt.Println("Image pulled successfully!")
	},
}

func GetInstallCommand() *cobra.Command {
	return installCmd
}
