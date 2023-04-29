import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.datasets as datasets
import torchvision.transforms
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from PIL.Image import Image
from model import Discriminator, Generator, initialize_weights, saveimage
import os



device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
learning_rate = 2e-4
batch_size = 128
image_size = 64
channels_img = 3
z_dim = 100
num_epochs = 5
features_disc = 64
features_gen = 64

transform = transforms.Compose(
    [
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize([0.5 for _ in range(channels_img)], [0.5 for _ in range(channels_img)]),
    ]
)

dataset = datasets.ImageFolder("venv/waifu", transform=transform)
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
gen = Generator(z_dim, channels_img, features_gen).to(device)
disc = Discriminator(channels_img, features_disc).to(device)
initialize_weights(gen)
initialize_weights(disc)

opt_gen = optim.Adam(gen.parameters(), lr=learning_rate, betas=(0.5, 0.999))
opt_disc = optim.Adam(disc.parameters(), lr=learning_rate, betas=(0.5, 0.999))
criterion = nn.BCELoss()

fixed_noise = torch.randn(32, z_dim, 1, 1).to(device)
writer_real = SummaryWriter(f"runs/real")
writer_fake = SummaryWriter(f"runs/fake")
step = 0

gen.train()
disc.train()

for epoch in range(num_epochs):
    for batch_idx, (real, _) in enumerate(loader):
        real = real.to(device)
        noise = torch.randn((batch_size, z_dim, 1, 1)).to(device)
        fake = gen(noise)
        disc_real = disc(real).reshape(-1)
        loss_disc_real = criterion(disc_real, torch.ones_like(disc_real))
        disc_fake = disc(fake).reshape(-1)
        loss_disc_fake = criterion(disc_fake, torch.zeros_like(disc_fake))
        loss_disc = (loss_disc_real + loss_disc_fake)/2
        disc.zero_grad()
        loss_disc.backward(retain_graph=True)
        opt_disc.step()

        output = disc(fake).reshape(-1)
        loss_gen = criterion(output, torch.ones_like(output))
        gen.zero_grad()
        loss_gen.backward()
        opt_gen.step()

        if batch_idx == 0 and epoch % 1 == 0:
            print(f"Epoch [{epoch}/{num_epochs}] Batch {batch_idx}/{len(loader)} \
            Loss D: {loss_disc:.4f}, loss_G: {loss_gen:.4f}"
            )

            with torch.no_grad():
                fake = gen(fixed_noise)
                img_grid_real = torchvision.utils.make_grid(
                    real[:32], normalize=True
                )
                img_grid_fake = torchvision.utils.make_grid(
                    fake[:32], normalize = True
                )
                writer_real.add_image("Real", img_grid_real, global_step=step)
                writer_fake.add_image("Fake", img_grid_fake, global_step=step)


            step += 1


saveimage(fake, "output/endresult/")
data = {
    "gen": gen.state_dict(),
    "disc": disc.state_dict(),
    "opt_gen": opt_gen.state_dict(),
    "opt_disc": opt_disc.state_dict(),
    "num_epochs": num_epochs,
    "z_dim": z_dim,
    "channels_img": channels_img,
    "transform": transform,
    "image_size": image_size,
    "features_gen": features_gen,
    "features_disc": features_disc,
}
torch.save(data, "data.pth")


















