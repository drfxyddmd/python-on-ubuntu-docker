name: MariaDB Demo

on:
  workflow_dispatch:
    inputs:
      imageName:
        description: 'Docker image name (e.g., mariadb:latest)'
        required: true
        default: 'mariadb:latest'

permissions: read-all

jobs:
  build:
    runs-on: ubuntu-latest
    environment: actions-cicd
    steps:
      - name: Ensure Python is installed
        run: |
          sudo apt-get update
          sudo apt-get install -y python3

      - name: Install the RapidFort CLI tools
        run: |
          curl https://frontrow.rapidfort.com/cli/ | bash
          echo "$HOME/.rapidfort/bin" >> $GITHUB_PATH

      - name: Authenticate with RapidFort
        env:
          RF_ACCESS_ID: ${{ secrets.RF_ACCESS_ID }}
          RF_SECRET_ACCESS_KEY: ${{ secrets.RF_SECRET_ACCESS_KEY }}
        run: rflogin

      - name: Pull the image specified by the user
        run: docker pull ${{ github.event.inputs.imageName }}

      - name: Run rfstub to generate the stub
        run: rfstub ${{ github.event.inputs.imageName }}

      - name: Run the stub container (basic startup check)
        run: |
          docker run -d --rm --cap-add=SYS_PTRACE --name my-rf-test ${{ github.event.inputs.imageName }}-rfstub
          sleep 15

      - name: Stop the stub container
        run: docker stop my-rf-test

      - name: Run rfharden to optimize and secure the image
        run: rfharden ${{ github.event.inputs.imageName }}-rfstub

      - name: Check out the images created
        run: docker images | grep ${{ github.event.inputs.imageName }}

      - name: Final message
        run: echo "Workflow completed successfully."
