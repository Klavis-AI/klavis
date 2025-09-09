package main

import (
	"fmt"
	"klavis/commands"

	"github.com/spf13/cobra"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "klavis",
		Short: "Klavis CLI tool",
	}

	rootCmd.AddCommand(commands.GetInstallCommand())
	rootCmd.AddCommand(commands.GetRunCommand())
	rootCmd.AddCommand(commands.GetImagesCommand())
	rootCmd.AddCommand(commands.GetUninstallCommand())

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
	}
}
