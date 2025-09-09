package commands

import (
	"fmt"
	"os/exec"
	"strings"

	"github.com/spf13/cobra"
)

var imageCmd = &cobra.Command{
	Use:   "images",
	Short: "Shows all tool from the Klavis",
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
		klavisImages := []string{}
		for _, line := range lines {
			if strings.Contains(line, "klavis-ai") {
				klavisImages = append(klavisImages, line)
			}
		}

		// Print results
		fmt.Println("Klavis images installed:")
		for _, img := range klavisImages {
			fmt.Println(img)
		}

		// Optional: print count
		fmt.Printf("Total Klavis images: %d\n", len(klavisImages))
	},
}

func GetImagesCommand() *cobra.Command {
	return imageCmd
}
