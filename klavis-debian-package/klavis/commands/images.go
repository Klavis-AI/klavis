package commands

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/spf13/cobra"
)

var imageCmd = &cobra.Command{
	Use:   "images",
	Short: "Shows all tool from the Klavis",
	Run: func(cmd *cobra.Command, args []string) {
		run := exec.Command("sh", "-c", `docker images --format "{{.Repository}}:{{.Tag}}" | grep klavis-ai`)
		run.Stdout = os.Stdout
		run.Stderr = os.Stderr
		run.Stdin = os.Stdin

		if err := run.Run(); err != nil {
			fmt.Println("Error running container:", err)
			return
		}
	},
}

func GetImagesCommand() *cobra.Command {
	return imageCmd
}
