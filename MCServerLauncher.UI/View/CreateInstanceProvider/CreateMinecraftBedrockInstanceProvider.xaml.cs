﻿using System;
using System.Windows;
using System.Windows.Controls;

namespace MCServerLauncher.UI.View.CreateInstanceProvider
{
    /// <summary>
    /// CreateMinecraftBedrockInstanceProvider.xaml 的交互逻辑
    /// </summary>
    public partial class CreateMinecraftBedrockInstanceProvider : UserControl
    {
        public CreateMinecraftBedrockInstanceProvider()
        {
            InitializeComponent();
        }
        private void GoPreCreateInstance(object sender, RoutedEventArgs e)
        {
            var parent = (CreateInstancePage)Parent;
            parent.CurrentCreateInstance.GoBack();
        }


        private void FinishSetup(object sender, RoutedEventArgs e)
        {
            return;
        }
    }
}